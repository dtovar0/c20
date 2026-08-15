from app import db
from app.modules.switch.models import SWITCH_TABLES as TEAMS_TABLES
import datetime

# El historial y el espejo del switch son compartidos con C20: ambas secciones
# operan sobre el mismo nodo, así que el estado del switch y el rastro de cada
# número son únicos. Lo propio de Teams son la cola, las tareas y los contadores.
from app.modules.switch.models import (
    SwitchHistory as TeamsHistory,
    SwitchSnpaname, SwitchTofcname, SwitchOfc2code, SwitchDnscrn,
)


class TeamsJob(db.Model):
    """
    TABLA MAESTRA (HEADER): Contiene la definición global de la carga.
    """
    __tablename__ = 'teams_jobs'

    id = db.Column(db.Integer, primary_key=True)
    # Indexado: los no-admin solo ven sus propias tareas, así que el listado
    # filtra siempre por usuario
    usuario = db.Column(db.String(100), nullable=False, index=True)
    tarea = db.Column(db.String(50)) # add / delete
    accion_tipo = db.Column(db.String(50))
    datos_tipo = db.Column(db.String(50)) # Archivo / Manual
    archivo_origen = db.Column(db.String(255))
    # Prefijo del lote (equivale a `actividades_teams.prefijo` del sistema legado).
    # Entra literalmente en el comando: 'DMOD INSRT <prefijo> XLT PX2 MSTEAMS2'.
    # El valor 100 es especial: conmuta a 'RTE DEST 16' en vez de insertar prefijo.
    prefijo = db.Column(db.String(3))
    # Cliente al que pertenece el lote (columna presente en el sistema legado)
    cliente = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, index=True)

    # Teams no tiene modo Force: el nodo nunca sobrescribe un registro existente.
    # Si ya existe, lo reporta como Fail y sigue.

    # Relación con sus fragmentos (chunks)
    tasks = db.relationship('TeamsTask', backref='job', lazy=True, cascade="all, delete-orphan")


class TeamsTask(db.Model):
    """
    TABLA DE EJECUCIÓN (CHUNKS): Uno por cada 200 registros.
    """
    __tablename__ = 'teams_tasks'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('teams_jobs.id'), nullable=False)

    chunk_index = db.Column(db.Integer, default=1)
    chunk_total = db.Column(db.Integer, default=1)

    datos = db.Column(db.Text) # Almacena los números (se limpia al terminar)
    # Indexado: el worker consulta por estado en cada ciclo del bucle
    estado = db.Column(db.String(50), default='Pendiente', index=True)

    fecha_inicio = db.Column(db.DateTime, index=True)
    fecha_fin = db.Column(db.DateTime)

    # Relación de reintento (para el sistema de complementarias)
    parent_id = db.Column(db.Integer, db.ForeignKey('teams_tasks.id'), nullable=True)
    tipo = db.Column(db.String(20), default='normal')

    # cascade delete-orphan: TeamsDetail.id es a la vez PK y FK, por lo que no
    # puede quedar huérfano con la FK a NULL; debe borrarse junto con su tarea.
    resumen = db.relationship('TeamsDetail', backref='task', uselist=False, lazy=True,
                              cascade="all, delete-orphan")
    # El historial NO cuelga de aquí: es compartido entre secciones y sobrevive
    # al borrado de la tarea, que es justo lo que lo hace útil como trazabilidad.
    command_logs = db.relationship('TeamsCommandLog', backref='task', lazy=True,
                                   cascade="all, delete-orphan")

    __table_args__ = (
        # Consulta del worker en cada ciclo: pendientes + programadas ya vencidas
        db.Index('ix_teams_tasks_estado_fecha', 'estado', 'fecha_inicio'),
    )

    def to_dict(self):
        job = self.job
        return {
            "id": self.id,
            "job_id": self.job_id,
            "usuario": job.usuario,
            "tarea": job.tarea,
            "estado": self.estado,
            "accion_tipo": job.accion_tipo,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "created_at": job.created_at.isoformat(),
            "datos_tipo": job.datos_tipo,
            "archivo_origen": job.archivo_origen,
            "chunk_index": self.chunk_index,
            "chunk_total": self.chunk_total,
            "prefijo": job.prefijo,
            "cliente": job.cliente,
            "resumen": self.resumen.to_dict() if self.resumen else TeamsDetail.empty_dict()
        }


class TeamsDetail(db.Model):
    """
    RESUMEN POR TAREA: un juego de contadores por cada tabla del switch.

    Cada tabla se recorre en una pasada independiente y produce su propio
    total/ok/fail, igual que la tabla `daemon_teams` del sistema legado.

    Semántica, uniforme en las cuatro tablas:
      OK   -> se ejecutó la operación (alta en 'add', baja en 'del')
      FAIL -> no se hizo nada porque el registro no estaba en el estado esperado
              (en 'add' ya existía; en 'del' no existía). No es un error.
    """
    __tablename__ = 'teams_details'
    id = db.Column(db.Integer, db.ForeignKey('teams_tasks.id'), primary_key=True)
    duracion = db.Column(db.Integer, default=0) # Segundos totales de la ejecución

    snpaname_total = db.Column(db.Integer, default=0)
    snpaname_ok = db.Column(db.Integer, default=0)
    snpaname_fail = db.Column(db.Integer, default=0)
    snpaname_log = db.Column(db.Text)

    tofcname_total = db.Column(db.Integer, default=0)
    tofcname_ok = db.Column(db.Integer, default=0)
    tofcname_fail = db.Column(db.Integer, default=0)
    tofcname_log = db.Column(db.Text)

    ofc2code_total = db.Column(db.Integer, default=0)
    ofc2code_ok = db.Column(db.Integer, default=0)
    ofc2code_fail = db.Column(db.Integer, default=0)
    ofc2code_log = db.Column(db.Text)

    dnscrn_total = db.Column(db.Integer, default=0)
    dnscrn_ok = db.Column(db.Integer, default=0)
    dnscrn_fail = db.Column(db.Integer, default=0)
    dnscrn_log = db.Column(db.Text)

    @staticmethod
    def empty_dict():
        base = {t: {"total": 0, "ok": 0, "fail": 0} for t in TEAMS_TABLES}
        base.update({"total": 0, "ok": 0, "fail": 0, "duracion": 0})
        return base

    def to_dict(self):
        """
        Devuelve el desglose por tabla más un consolidado.

        El consolidado usa OFC2CODE como referencia: es la tabla por la que pasa
        cada número exactamente una vez, tanto en 'add' como en 'del' (SNPANAME y
        TOFCNAME operan sobre ladas/series deduplicadas, así que sus totales no
        son comparables con la cantidad de números del lote).
        """
        data = {
            t: {
                "total": getattr(self, f"{t}_total") or 0,
                "ok": getattr(self, f"{t}_ok") or 0,
                "fail": getattr(self, f"{t}_fail") or 0,
            } for t in TEAMS_TABLES
        }
        data["duracion"] = self.duracion or 0
        data.update({
            "total": data["ofc2code"]["total"],
            "ok": data["ofc2code"]["ok"],
            "fail": data["ofc2code"]["fail"],
        })
        return data

    def logs_dict(self):
        """Logs crudos por tabla (se sirven aparte: son grandes y solo se usan en el detalle)."""
        return {t: getattr(self, f"{t}_log") or "" for t in TEAMS_TABLES}


class TeamsCommandLog(db.Model):
    """
    LOG DE COMANDOS (FULL FLOW): Almacena la interacción cruda de la sesión.
    """
    __tablename__ = 'teams_command_logs'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('teams_tasks.id'), nullable=False)
    raw_log = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "raw_log": self.raw_log,
            "fecha": self.fecha.isoformat() if self.fecha else None
        }
