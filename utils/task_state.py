"""Consulta y cambia el estado de una tarea concreta (PSX5K, C20 o Teams).

Existe para el caso que la web no cubre: una tarea que quedó en 'Ejecutando'
porque el worker murió a mitad del ciclo. Esas tareas están huérfanas —nadie las
está procesando— pero el estado en base dice lo contrario, así que el watchdog
sigue alertando y la cola no las vuelve a tomar.

Uso:

    # Ver el estado actual (no modifica nada)
    python3 utils/task_state.py psx 129

    # Reponer en cola para que el worker la recoja
    python3 utils/task_state.py psx 129 --estado Pendiente

    # Varias a la vez: IDs sueltos, rangos o ambos (una sola confirmación)
    python3 utils/task_state.py c20 120-124 --estado Pendiente
    python3 utils/task_state.py c20 120 122 130-132 --estado Pendiente

    # Por fecha de ejecución (fecha_inicio). --to es 'now' si se omite.
    python3 utils/task_state.py c20 --from 2026-10-01 --estado Pendiente
    python3 utils/task_state.py c20 --from "2026-10-20 08:00" --to "2026-10-20 12:30" --estado Pendiente

    Al cambiar el estado por fechas solo se toman las tareas en
    ESTADOS_REINTENTABLES ('Terminado con Errores' y 'Error'), para no volver a
    poner en cola las completadas; --solo indica otros estados.

    # Listar lo que está colgado en 'Ejecutando'
    python3 utils/task_state.py psx --colgadas

Estados válidos: los que ya usan los módulos —Pendiente, Programada, Ejecutando,
Cancelada, Error, Completado, Terminado con Errores, Abortada.

OJO: si el worker está vivo y realmente procesando la tarea, cambiar el estado a
mano puede provocar una segunda ejecución del mismo lote sobre el nodo. El script
avisa cuando la tarea lleva poco tiempo en ejecución, pero la comprobación de que
el worker está detenido es tuya.
"""
import argparse
import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db

# Estados que los módulos usan en sus transiciones (app/modules/*/routes.py).
ESTADOS_VALIDOS = [
    'Pendiente', 'Programada', 'Ejecutando', 'Activa', 'Cancelada', 'Cancelado',
    'Error', 'Completado', 'Completada', 'Terminado con Errores', 'Abortada',
]

# Umbral por debajo del cual se asume que el worker podría estar trabajando.
MINUTOS_SOSPECHA = 5

# Estados que se toman por defecto al cambiar por fechas: los que terminaron
# sin aplicar todo. Un rango de fechas también abarca las completadas, y
# reponerlas en cola repetiría lotes ya aplicados.
ESTADOS_REINTENTABLES = ['Terminado con Errores', 'Error']

FORMATOS_FECHA = ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d')


def _resolver_modelo(modulo):
    if modulo == 'psx':
        from app.modules.psx.models import PSX5KTask
        return PSX5KTask, 'PSX5K'
    if modulo == 'c20':
        from app.modules.c20.models import C20Task
        return C20Task, 'C20'
    if modulo == 'teams':
        from app.modules.teams.models import TeamsTask
        return TeamsTask, 'Teams'
    raise ValueError(f"Módulo desconocido: {modulo}")


def _antiguedad(task):
    """Minutos desde que arrancó, o None si no tiene fecha_inicio."""
    if not task.fecha_inicio:
        return None
    return (datetime.datetime.now() - task.fecha_inicio).total_seconds() / 60


def _describir(task, etiqueta):
    mins = _antiguedad(task)
    print(f"   Tarea {etiqueta} #{task.id}")
    print(f"   Estado       : {task.estado}")
    print(f"   Job          : {task.job_id}")
    print(f"   Fecha inicio : {task.fecha_inicio or '-'}")
    if mins is not None:
        print(f"   En ese estado: {mins:.0f} min")


def listar_colgadas(modelo, etiqueta):
    tareas = modelo.query.filter(modelo.estado == 'Ejecutando').order_by(modelo.id).all()
    if not tareas:
        print(f"✅ No hay tareas de {etiqueta} en estado 'Ejecutando'.")
        return
    print(f"⚠️  {len(tareas)} tarea(s) de {etiqueta} en 'Ejecutando':\n")
    for t in tareas:
        mins = _antiguedad(t)
        edad = f"{mins:.0f} min" if mins is not None else "sin fecha_inicio"
        print(f"   #{t.id:<8} job={t.job_id:<8} desde hace {edad}")
    print(f"\nPara reponer una en cola:\n   python3 utils/task_state.py <modulo> <id> --estado Pendiente")


def parse_ids(tokens):
    """
    Convierte '120', '120-124' y '120,122' en una lista ordenada de IDs únicos.

    Lanza ValueError con el token culpable si alguno no es válido.
    """
    ids = set()
    for token in tokens:
        for parte in token.split(','):
            parte = parte.strip()
            if not parte:
                continue
            try:
                if '-' in parte:
                    inicio, fin = (int(x) for x in parte.split('-', 1))
                    if inicio > fin:
                        raise ValueError
                    ids.update(range(inicio, fin + 1))
                else:
                    ids.add(int(parte))
            except ValueError:
                raise ValueError(f"ID o rango no válido: '{parte}'")
    return sorted(ids)


def parse_fecha(texto, fin_del_dia=False):
    """
    Acepta 'now', 'AAAA-MM-DD', 'AAAA-MM-DD HH:MM' o 'AAAA-MM-DD HH:MM:SS'.

    Una fecha sin hora es el inicio del día, o su último instante si
    fin_del_dia (para que --to 2026-10-20 incluya ese día completo).
    """
    texto = texto.strip()
    if texto.lower() == 'now':
        return datetime.datetime.now()
    for formato in FORMATOS_FECHA:
        try:
            fecha = datetime.datetime.strptime(texto, formato)
        except ValueError:
            continue
        if formato == '%Y-%m-%d' and fin_del_dia:
            fecha = fecha.replace(hour=23, minute=59, second=59, microsecond=999999)
        return fecha
    raise ValueError(f"Fecha no válida: '{texto}'. Usa now, AAAA-MM-DD o 'AAAA-MM-DD HH:MM'")


def ids_por_fechas(modelo, desde, hasta, estados=None):
    """IDs de las tareas con fecha_inicio en [desde, hasta], opcionalmente por estado."""
    query = modelo.query.filter(modelo.fecha_inicio >= desde, modelo.fecha_inicio <= hasta)
    if estados:
        query = query.filter(modelo.estado.in_(estados))
    return [t.id for t in query.order_by(modelo.id).all()]


def cambiar_estado(modelo, etiqueta, task_ids, nuevo_estado, forzar):
    """
    Cambia el estado de una o varias tareas con una sola confirmación.

    Las que no existen, ya están en el estado pedido o parecen en proceso se
    informan y se omiten; el resto se cambia en un único commit.
    """
    a_cambiar, omitidas = [], []
    for task_id in task_ids:
        task = db.session.get(modelo, task_id)
        if not task:
            omitidas.append(f"#{task_id}: no existe")
            continue
        if task.estado == nuevo_estado:
            omitidas.append(f"#{task_id}: ya está en '{nuevo_estado}'")
            continue
        # Aviso si parece que el worker sigue trabajando en ella.
        mins = _antiguedad(task)
        if task.estado == 'Ejecutando' and mins is not None and mins < MINUTOS_SOSPECHA and not forzar:
            omitidas.append(f"#{task_id}: lleva solo {mins:.0f} min en ejecución "
                            "(el worker podría estar procesándola; usa --forzar si está huérfana)")
            continue
        a_cambiar.append(task)

    if len(task_ids) == 1 and a_cambiar:
        print(f"\n📋 Estado actual:")
        _describir(a_cambiar[0], etiqueta)

    if omitidas:
        print(f"\n⏭️  Se omiten {len(omitidas)}:")
        for motivo in omitidas:
            print(f"   {motivo}")

    if not a_cambiar:
        print("\nℹ️  No hay tareas que cambiar.")
        # Solo es un error si alguna no existe o estaba en proceso; que ya
        # estuvieran en el estado pedido no lo es.
        return 0 if all("ya está en" in m for m in omitidas) else 1

    print(f"\n🔄 Cambio propuesto ({len(a_cambiar)} tarea(s) de {etiqueta}) -> '{nuevo_estado}':")
    for task in a_cambiar:
        print(f"   #{task.id:<8} {task.estado}")
    if nuevo_estado in ('Pendiente', 'Programada'):
        print("    fecha_inicio se limpiará para que el worker las tome como nuevas.")

    confirm = input("\n¿Confirmas el cambio? (escribe 'si'): ")
    if confirm.strip().lower() != 'si':
        print("Operación cancelada.")
        return 0

    anteriores = {}
    for task in a_cambiar:
        anteriores[task.id] = task.estado
        task.estado = nuevo_estado
        # Reponer en cola sin limpiar la fecha dejaría al watchdog contando desde
        # el arranque viejo y volvería a alertar de inmediato.
        if nuevo_estado in ('Pendiente', 'Programada'):
            task.fecha_inicio = None
    db.session.commit()

    # Queda constancia: un cambio de estado a mano es justo lo que uno quiere
    # encontrar en la auditoría cuando después revisa qué pasó con la tarea.
    try:
        from app.modules.audit.services import add_audit_log
        for task_id, anterior in anteriores.items():
            add_audit_log(
                f"CAMBIO MANUAL DE ESTADO ({etiqueta}-{task_id})",
                status="warning",
                detail=f"{anterior} -> {nuevo_estado} | Ejecutado con utils/task_state.py",
                user_override="SYSTEM_CLI",
            )
    except Exception as e:
        print(f"⚠️  El estado se cambió, pero no se pudo registrar en auditoría: {e}")

    print()
    for task_id, anterior in anteriores.items():
        print(f"✅ Tarea #{task_id}: '{anterior}' -> '{nuevo_estado}'")
    if nuevo_estado == 'Pendiente':
        print("   El worker las recogerá en sus próximos ciclos, una a la vez.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Consulta o cambia el estado de una tarea (PSX5K, C20, Teams).")
    parser.add_argument('modulo', choices=['psx', 'c20', 'teams'])
    parser.add_argument('task_ids', nargs='*',
                        help="ID(s) de tarea: sueltos, rangos (120-124) o separados por coma")
    parser.add_argument('--estado', help=f"Nuevo estado. Válidos: {', '.join(ESTADOS_VALIDOS)}")
    parser.add_argument('--from', dest='desde',
                        help="Desde esta fecha de ejecución: AAAA-MM-DD o 'AAAA-MM-DD HH:MM'")
    parser.add_argument('--to', dest='hasta', default='now',
                        help="Hasta esta fecha de ejecución (por defecto: now)")
    parser.add_argument('--solo', nargs='+', metavar='ESTADO',
                        help="Con --from: solo tareas en estos estados. Al cambiar, por "
                             f"defecto {', '.join(ESTADOS_REINTENTABLES)}")
    parser.add_argument('--colgadas', action='store_true',
                        help="Lista las tareas en 'Ejecutando' y termina")
    parser.add_argument('--forzar', action='store_true',
                        help="Omite el aviso de tarea recién iniciada")
    args = parser.parse_args()

    if args.estado and args.estado not in ESTADOS_VALIDOS:
        parser.error(f"Estado no válido: '{args.estado}'.\nVálidos: {', '.join(ESTADOS_VALIDOS)}")
    for estado in args.solo or []:
        if estado not in ESTADOS_VALIDOS:
            parser.error(f"Estado no válido en --solo: '{estado}'.\nVálidos: {', '.join(ESTADOS_VALIDOS)}")
    if args.desde and args.task_ids:
        parser.error("Usa IDs o --from/--to, no ambos.")
    if args.solo and not args.desde:
        parser.error("--solo solo aplica junto con --from.")
    if not args.colgadas and not args.task_ids and not args.desde:
        parser.error("Indica un ID de tarea, --from <fecha>, o usa --colgadas.")
    try:
        task_ids = parse_ids(args.task_ids)
        if args.desde:
            desde = parse_fecha(args.desde)
            hasta = parse_fecha(args.hasta, fin_del_dia=True)
            if desde > hasta:
                raise ValueError(f"--from ({desde:%Y-%m-%d %H:%M}) es posterior a --to ({hasta:%Y-%m-%d %H:%M})")
    except ValueError as e:
        parser.error(str(e))

    app = create_app()
    with app.app_context():
        modelo, etiqueta = _resolver_modelo(args.modulo)

        print("=" * 60)
        print(f"🗂  ESTADO DE TAREAS — {etiqueta}")
        print("=" * 60)

        if args.colgadas:
            listar_colgadas(modelo, etiqueta)
            return 0

        if args.desde:
            # Consultar muestra todo el rango; cambiar se limita por defecto a
            # los estados reintentables.
            estados = args.solo or (ESTADOS_REINTENTABLES if args.estado else None)
            task_ids = ids_por_fechas(modelo, desde, hasta, estados)
            filtro = f" | estados: {', '.join(estados)}" if estados else ""
            print(f"📅 Ejecutadas entre {desde:%Y-%m-%d %H:%M} y {hasta:%Y-%m-%d %H:%M}{filtro}")
            if not task_ids:
                print("\nℹ️  Ninguna tarea en ese rango.")
                return 0

        if not args.estado:
            # Sin --estado el script solo informa: consultar no debe modificar.
            faltantes = 0
            for task_id in task_ids:
                task = db.session.get(modelo, task_id)
                if not task:
                    print(f"\n❌ No existe la tarea {etiqueta} #{task_id}.")
                    faltantes += 1
                    continue
                print()
                _describir(task, etiqueta)
            print("\nPara cambiarlo, añade --estado <nuevo estado>.")
            return 1 if faltantes else 0

        return cambiar_estado(modelo, etiqueta, task_ids, args.estado, args.forzar)


if __name__ == '__main__':
    sys.exit(main())
