"""
Estadísticas agregadas de todas las secciones operativas (PSX5K, C20 y Teams).

Los dashboards mostraban solo PSX5K porque era la única sección cuando se
construyeron. Este módulo consulta las tres y devuelve cada cifra con su
desglose por sección, de modo que el panel pueda presentar el total y el
reparto sin que el frontend tenga que llamar a tres endpoints y sumarlos.

Cada sección aporta sus propios modelos; lo que cambia entre ellas es dónde
viven las tareas y cómo se cuentan los registros procesados:

  PSX5K -> opera número por número y colapsa todo en un contador (detail.total)
  C20   -> cuatro pasadas por tabla; OFC2CODE es la referencia del lote, la
           única tabla por la que cada número pasa exactamente una vez
  Teams -> igual que C20
"""
from sqlalchemy import func
from app import db

# Estados que cuentan como tarea terminada, en cualquier sección
ESTADOS_TERMINADOS = ['Completado', 'Terminado con Errores']


def _secciones():
    """
    Devuelve la configuración de cada sección.

    Se importa aquí y no arriba para evitar ciclos: los módulos de sección
    importan a su vez desde core.
    """
    from app.modules.psx.models import PSX5KJob, PSX5KTask, PSX5KDetail
    from app.modules.c20.models import C20Job, C20Task, C20Detail
    from app.modules.teams.models import TeamsJob, TeamsTask, TeamsDetail

    return [
        {
            'key': 'psx5k', 'label': 'PSX5K',
            'job': PSX5KJob, 'task': PSX5KTask, 'detail': PSX5KDetail,
            # PSX5K lleva un solo juego de contadores
            'col_total': PSX5KDetail.total,
            'col_ok': PSX5KDetail.ok,
            'col_fail': PSX5KDetail.fail,
        },
        {
            'key': 'c20', 'label': 'C20',
            'job': C20Job, 'task': C20Task, 'detail': C20Detail,
            # En C20/Teams las cifras del lote son las de OFC2CODE
            'col_total': C20Detail.ofc2code_total,
            'col_ok': C20Detail.ofc2code_ok,
            'col_fail': C20Detail.ofc2code_fail,
        },
        {
            'key': 'teams', 'label': 'Teams',
            'job': TeamsJob, 'task': TeamsTask, 'detail': TeamsDetail,
            'col_total': TeamsDetail.ofc2code_total,
            'col_ok': TeamsDetail.ofc2code_ok,
            'col_fail': TeamsDetail.ofc2code_fail,
        },
    ]


def _vacio():
    """Estructura base de una métrica con desglose."""
    return {'total': 0, 'por_seccion': {}}


def _sumar(metrica, key, valor):
    """Acumula el valor de una sección en una métrica con desglose."""
    valor = int(valor or 0)
    metrica['por_seccion'][key] = valor
    metrica['total'] += valor


def stats_usuario(email):
    """
    Métricas del usuario indicado, con desglose por sección.

    Cada cifra trae su total y el reparto: {'total': 850, 'por_seccion':
    {'psx5k': 400, 'c20': 300, 'teams': 150}}.
    """
    from datetime import datetime
    hoy = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    tareas = _vacio()
    pendientes = _vacio()
    programadas = _vacio()
    volumen_hoy = _vacio()
    procesadas = _vacio()
    ok_hoy = _vacio()
    fail_hoy = _vacio()

    activa = None
    ultimas = []

    for cfg in _secciones():
        Job, Task, Detail = cfg['job'], cfg['task'], cfg['detail']
        key = cfg['key']
        base = Task.query.join(Job).filter(Job.usuario == email)

        _sumar(tareas, key, base.count())
        _sumar(pendientes, key, base.filter(Task.estado == 'Pendiente').count())
        _sumar(programadas, key, base.filter(Task.estado == 'Programada').count())
        _sumar(procesadas, key, base.filter(Task.estado.in_(ESTADOS_TERMINADOS)).count())

        vol = db.session.query(func.sum(cfg['col_total'])).join(
            Task, Task.id == Detail.id
        ).join(Job).filter(
            Job.usuario == email, Task.fecha_inicio >= hoy
        ).scalar()
        _sumar(volumen_hoy, key, vol)

        agg = db.session.query(
            func.sum(cfg['col_ok']), func.sum(cfg['col_fail'])
        ).join(Task, Task.id == Detail.id).join(Job).filter(
            Job.usuario == email,
            Task.estado.in_(ESTADOS_TERMINADOS),
            Task.fecha_inicio >= hoy
        ).first()
        _sumar(ok_hoy, key, agg[0] if agg else 0)
        _sumar(fail_hoy, key, agg[1] if agg else 0)

        # Tarea activa: solo puede haber una en todo el sistema, porque el nodo
        # admite una única conexión. Se anota de qué sección es.
        if activa is None:
            corriendo = Task.query.filter(Task.estado == 'Ejecutando') \
                                  .order_by(Task.id.desc()).first()
            if corriendo:
                activa = {'id': corriendo.id, 'seccion': cfg['label']}

        # Últimas terminadas del usuario, para la gráfica de historial
        for t in Task.query.join(Job).filter(
            Job.usuario == email, Task.estado.in_(ESTADOS_TERMINADOS)
        ).order_by(Task.id.desc()).limit(7).all():
            r = t.resumen
            if key == 'psx5k':
                ok, fail, total = (r.ok, r.fail, r.total) if r else (0, 0, 0)
            else:
                ok, fail, total = ((r.ofc2code_ok, r.ofc2code_fail, r.ofc2code_total)
                                   if r else (0, 0, 0))
            ultimas.append({'id': t.id, 'seccion': cfg['label'],
                            'ok': ok or 0, 'fail': fail or 0, 'total': total or 0,
                            'orden': t.fecha_fin or t.fecha_inicio})

    total_p = ok_hoy['total'] + fail_hoy['total']
    eficiencia = (ok_hoy['total'] / total_p * 100) if total_p else 0.0

    # Las últimas 7 de todas las secciones, por fecha real
    ultimas.sort(key=lambda x: (x['orden'] is None, x['orden']))
    ultimas = [{k: v for k, v in u.items() if k != 'orden'} for u in ultimas[-7:]]

    return {
        'total': tareas,
        'pending': pendientes,
        'scheduled': programadas,
        'processed_total': procesadas,
        'volume_today': volumen_hoy,
        'efficiency': round(eficiencia, 1),
        'active_task': activa['id'] if activa else 'NINGUNA',
        'active_section': activa['seccion'] if activa else None,
        'breakdown': {'ok': ok_hoy['total'], 'fail': fail_hoy['total']},
        'breakdown_por_seccion': {'ok': ok_hoy['por_seccion'],
                                  'fail': fail_hoy['por_seccion']},
        'last_7_tasks': ultimas,
        'secciones': [c['label'] for c in _secciones()],
    }


def stats_globales():
    """
    Métricas de todo el sistema para el dashboard de administrador, con
    desglose por sección.
    """
    from datetime import datetime, timedelta
    from sqlalchemy import case
    from app.modules.auth.models import User

    hoy = datetime.now().date()
    hace_7 = datetime.now() - timedelta(days=7)

    tareas = _vacio()
    pendientes = _vacio()
    programadas = _vacio()
    cola = _vacio()
    procesado_total = _vacio()
    volumen_hoy = _vacio()

    activa = None
    breakdown_hoy = {'ok': 0, 'fail': 0}
    # Serie diaria por sección, para la gráfica de tendencia apilada
    diario = {}
    # Recuento por estado y sección, para la dona
    estados = {'Completado': _vacio(), 'Ejecutando': _vacio(),
               'Pendiente': _vacio(), 'Error': _vacio()}
    top_users = {}

    for cfg in _secciones():
        Job, Task, Detail = cfg['job'], cfg['task'], cfg['detail']
        key, label = cfg['key'], cfg['label']

        _sumar(tareas, key, Task.query.count())
        _sumar(pendientes, key, Task.query.filter(Task.estado == 'Pendiente').count())
        _sumar(programadas, key, Task.query.filter(Task.estado == 'Programada').count())
        _sumar(cola, key, db.session.query(Task.job_id).filter(
            Task.estado.in_(['Programada', 'Pendiente', 'Ejecutando'])
        ).distinct().count())

        _sumar(procesado_total, key, db.session.query(func.sum(cfg['col_total'])).join(
            Task, Task.id == Detail.id
        ).filter(Task.estado == 'Completado').scalar())

        _sumar(volumen_hoy, key, db.session.query(func.sum(cfg['col_total'])).join(
            Task, Task.id == Detail.id
        ).join(Job).filter(func.date(Job.created_at) == hoy).scalar())

        agg = db.session.query(
            func.sum(cfg['col_ok']), func.sum(cfg['col_fail'])
        ).join(Task, Task.id == Detail.id).join(Job).filter(
            func.date(Job.created_at) == hoy
        ).first()
        breakdown_hoy['ok'] += int((agg[0] if agg else 0) or 0)
        breakdown_hoy['fail'] += int((agg[1] if agg else 0) or 0)

        if activa is None:
            corriendo = Task.query.filter(Task.estado == 'Ejecutando') \
                                  .order_by(Task.id.desc()).first()
            if corriendo:
                activa = {'id': corriendo.id, 'seccion': label,
                          'nombre': (corriendo.job.tarea or 'N/A').upper()}

        # Tareas por día y sección
        for d in db.session.query(
            func.date(Job.created_at).label('dia'), func.count(Job.id)
        ).filter(Job.created_at >= hace_7).group_by('dia').all():
            diario.setdefault(str(d[0]), {})[key] = int(d[1] or 0)

        # Estados de hoy
        for est, cnt in db.session.query(Task.estado, func.count(Task.id)).join(Job).filter(
            func.date(Job.created_at) == hoy
        ).group_by(Task.estado).all():
            cnt = int(cnt or 0)
            if est in ('Pendiente', 'Programada'):
                estados['Pendiente']['por_seccion'][key] = estados['Pendiente']['por_seccion'].get(key, 0) + cnt
                estados['Pendiente']['total'] += cnt
            elif est == 'Ejecutando':
                estados['Ejecutando']['por_seccion'][key] = estados['Ejecutando']['por_seccion'].get(key, 0) + cnt
                estados['Ejecutando']['total'] += cnt
            elif est == 'Terminado con Errores':
                estados['Error']['por_seccion'][key] = estados['Error']['por_seccion'].get(key, 0) + cnt
                estados['Error']['total'] += cnt
            elif est == 'Completado':
                estados['Completado']['por_seccion'][key] = estados['Completado']['por_seccion'].get(key, 0) + cnt
                estados['Completado']['total'] += cnt

        # Actividad por usuario, acumulada entre secciones
        for usuario, n in db.session.query(Job.usuario, func.count(Job.id)) \
                                    .group_by(Job.usuario).all():
            top_users.setdefault(usuario, {})[key] = int(n or 0)

    meses_es = {'Jan': 'Ene', 'Apr': 'Abr', 'Aug': 'Ago', 'Dec': 'Dic'}

    def fmt_dia(cadena):
        d = datetime.strptime(cadena, '%Y-%m-%d')
        mes = d.strftime('%b')
        return f"{d.strftime('%d')} {meses_es.get(mes, mes)}"

    dias = sorted(diario.keys())
    claves = [c['key'] for c in _secciones()]
    daily_tasks = {
        'days': [fmt_dia(d) for d in dias],
        'series': {k: [diario.get(d, {}).get(k, 0) for d in dias] for k in claves},
        'total': [sum(diario.get(d, {}).values()) for d in dias],
    }

    # Top 5 usuarios por actividad total, con su reparto por sección
    top = sorted(top_users.items(), key=lambda kv: sum(kv[1].values()), reverse=True)[:5]
    top_users_data = {
        'users': [u for u, _ in top],
        'series': {k: [datos.get(k, 0) for _, datos in top] for k in claves},
    }

    return {
        'users': User.query.count(),
        'tasks': tareas,
        'total': tareas,
        'pending': pendientes,
        'scheduled': programadas,
        'queue': cola,
        'processed_total': procesado_total,
        'volume_today': volumen_hoy,
        'breakdown': breakdown_hoy,
        'active_id': activa['id'] if activa else None,
        'active_task': str(activa['id']) if activa else 'NINGUNA',
        'active_name': activa['nombre'] if activa else None,
        'active_section': activa['seccion'] if activa else None,
        'daily_tasks': daily_tasks,
        'today_stats': {
            'labels': ['Completado', 'Ejecutando', 'Pendiente', 'Error'],
            'total': [estados['Completado']['total'], estados['Ejecutando']['total'],
                      estados['Pendiente']['total'], estados['Error']['total']],
            'por_seccion': {k: [estados[e]['por_seccion'].get(k, 0)
                                for e in ['Completado', 'Ejecutando', 'Pendiente', 'Error']]
                            for k in claves},
        },
        'top_users': top_users_data,
        'secciones': [{'key': c['key'], 'label': c['label']} for c in _secciones()],
    }
