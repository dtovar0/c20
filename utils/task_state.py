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


def cambiar_estado(modelo, etiqueta, task_id, nuevo_estado, forzar):
    task = db.session.get(modelo, task_id)
    if not task:
        print(f"❌ No existe la tarea {etiqueta} #{task_id}.")
        return 1

    print(f"\n📋 Estado actual:")
    _describir(task, etiqueta)

    if task.estado == nuevo_estado:
        print(f"\nℹ️  Ya está en '{nuevo_estado}'. Sin cambios.")
        return 0

    # Aviso si parece que el worker sigue trabajando en ella.
    mins = _antiguedad(task)
    if task.estado == 'Ejecutando' and mins is not None and mins < MINUTOS_SOSPECHA and not forzar:
        print(f"\n⚠️  Lleva solo {mins:.0f} min en ejecución: el worker podría estar")
        print("    procesándola ahora mismo. Detén el worker antes de continuar, o")
        print("    repite con --forzar si sabes que está huérfana.")
        return 1

    print(f"\n🔄 Cambio propuesto: '{task.estado}' -> '{nuevo_estado}'")
    if nuevo_estado in ('Pendiente', 'Programada'):
        print("    fecha_inicio se limpiará para que el worker la tome como nueva.")

    confirm = input("\n¿Confirmas el cambio? (escribe 'si'): ")
    if confirm.strip().lower() != 'si':
        print("Operación cancelada.")
        return 0

    anterior = task.estado
    task.estado = nuevo_estado
    # Reponer en cola sin limpiar la fecha dejaría al watchdog contando desde el
    # arranque viejo y volvería a alertar de inmediato.
    if nuevo_estado in ('Pendiente', 'Programada'):
        task.fecha_inicio = None
    db.session.commit()

    # Queda constancia: un cambio de estado a mano es justo lo que uno quiere
    # encontrar en la auditoría cuando después revisa qué pasó con la tarea.
    try:
        from app.modules.audit.services import add_audit_log
        add_audit_log(
            f"CAMBIO MANUAL DE ESTADO ({etiqueta}-{task_id})",
            status="warning",
            detail=f"{anterior} -> {nuevo_estado} | Ejecutado con utils/task_state.py",
            user_override="SYSTEM_CLI",
        )
    except Exception as e:
        print(f"⚠️  El estado se cambió, pero no se pudo registrar en auditoría: {e}")

    print(f"\n✅ Tarea #{task_id}: '{anterior}' -> '{nuevo_estado}'")
    if nuevo_estado == 'Pendiente':
        print("   El worker la recogerá en su próximo ciclo.")
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Consulta o cambia el estado de una tarea (PSX5K, C20, Teams).")
    parser.add_argument('modulo', choices=['psx', 'c20', 'teams'])
    parser.add_argument('task_id', nargs='?', type=int, help="ID de la tarea")
    parser.add_argument('--estado', help=f"Nuevo estado. Válidos: {', '.join(ESTADOS_VALIDOS)}")
    parser.add_argument('--colgadas', action='store_true',
                        help="Lista las tareas en 'Ejecutando' y termina")
    parser.add_argument('--forzar', action='store_true',
                        help="Omite el aviso de tarea recién iniciada")
    args = parser.parse_args()

    if args.estado and args.estado not in ESTADOS_VALIDOS:
        parser.error(f"Estado no válido: '{args.estado}'.\nVálidos: {', '.join(ESTADOS_VALIDOS)}")
    if not args.colgadas and args.task_id is None:
        parser.error("Indica un ID de tarea, o usa --colgadas.")

    app = create_app()
    with app.app_context():
        modelo, etiqueta = _resolver_modelo(args.modulo)

        print("=" * 60)
        print(f"🗂  ESTADO DE TAREAS — {etiqueta}")
        print("=" * 60)

        if args.colgadas:
            listar_colgadas(modelo, etiqueta)
            return 0

        if not args.estado:
            # Sin --estado el script solo informa: consultar no debe modificar.
            task = db.session.get(modelo, args.task_id)
            if not task:
                print(f"❌ No existe la tarea {etiqueta} #{args.task_id}.")
                return 1
            print()
            _describir(task, etiqueta)
            print("\nPara cambiarlo, añade --estado <nuevo estado>.")
            return 0

        return cambiar_estado(modelo, etiqueta, args.task_id, args.estado, args.forzar)


if __name__ == '__main__':
    sys.exit(main())
