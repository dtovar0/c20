from app import db
import datetime

class C20Job(db.Model):
    """
    TABLA MAESTRA (HEADER): Contiene la definición global de la carga.
    """
    __tablename__ = 'c20_jobs'

    id = db.Column(db.Integer, primary_key=True)
    # Indexado: los no-admin solo ven sus propias tareas, así que el listado
    # filtra siempre por usuario
    usuario = db.Column(db.String(100), nullable=False, index=True)
    tarea = db.Column(db.String(50)) # add / delete
    accion_tipo = db.Column(db.String(50)) # bulk / etc
    datos_tipo = db.Column(db.String(50)) # Archivo / Manual
    archivo_origen = db.Column(db.String(255))
    # Zona operativa del lote (equivale a `actividades.zona` del sistema legado).
    # Se escribe como 2º campo de c20_num.exp; el valor 900 conmuta OFC2CODE a TRMT OFC UNDN.
    zona = db.Column(db.String(5))
    created_at = db.Column(db.DateTime, default=datetime.datetime.now, index=True)

    # C20 no tiene modo Force: los .exp nunca sobrescriben un registro existente.
    # Si ya existe, lo reportan como Fail y siguen. Por eso no hay columna run_force.

    # Relación con sus fragmentos (chunks)
    tasks = db.relationship('C20Task', backref='job', lazy=True, cascade="all, delete-orphan")

class C20Task(db.Model):
    """
    TABLA DE EJECUCIÓN (CHUNKS): Uno por cada 200 registros.
    """
    __tablename__ = 'c20_tasks'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('c20_jobs.id'), nullable=False)

    chunk_index = db.Column(db.Integer, default=1)
    chunk_total = db.Column(db.Integer, default=1)

    datos = db.Column(db.Text) # Almacena los números (se limpia al terminar)
    # Indexado: el worker consulta por estado en cada ciclo del bucle
    estado = db.Column(db.String(50), default='Pendiente', index=True)

    fecha_inicio = db.Column(db.DateTime, index=True)
    fecha_fin = db.Column(db.DateTime)

    # Relación de reintento (para el sistema de complementarias)
    parent_id = db.Column(db.Integer, db.ForeignKey('c20_tasks.id'), nullable=True)
    tipo = db.Column(db.String(20), default='normal')

    # Relación con el detalle (1 a 1)
    # cascade delete-orphan: C20Detail.id es a la vez PK y FK, por lo que no puede
    # quedar huérfano con la FK a NULL; debe borrarse junto con su tarea.
    resumen = db.relationship('C20Detail', backref='task', uselist=False, lazy=True,
                              cascade="all, delete-orphan")
    # Los logs se borran con la tarea: sin cascade, la FK impide eliminarla.
    # El historial NO cuelga de aquí: es compartido entre secciones y sobrevive
    # al borrado de la tarea, que es justo lo que lo hace útil como trazabilidad.
    command_logs = db.relationship('C20CommandLog', backref='task', lazy=True,
                                   cascade="all, delete-orphan")

    __table_args__ = (
        # Consulta del worker en cada ciclo: pendientes + programadas ya vencidas
        db.Index('ix_c20_tasks_estado_fecha', 'estado', 'fecha_inicio'),
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
            "zona": job.zona,
            "resumen": self.resumen.to_dict() if self.resumen else C20Detail.empty_dict()
        }

# Definidas en shared_models: son comunes a todas las secciones de la plataforma
from app.modules.c20.shared_models import C20_TABLES, C20_DEL_TABLES  # noqa: F401

class C20Detail(db.Model):
    """
    RESUMEN POR TAREA: un juego de contadores por cada tabla del C20.

    A diferencia de PSX5K (que opera número por número en una sola sesión y colapsa
    todo en un contador), C20 hace una pasada independiente por tabla, así que cada
    una produce su propio total/ok/fail y su propio log crudo.

    Semántica de los .exp, uniforme en las cuatro tablas:
      OK   -> se ejecutó la operación (alta en 'add', baja en 'del')
      FAIL -> no se hizo nada porque el registro no estaba en el estado esperado
              (en 'add' ya existía; en 'del' no existía). No es un error de ejecución.
    """
    __tablename__ = 'c20_details'
    id = db.Column(db.Integer, db.ForeignKey('c20_tasks.id'), primary_key=True)
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
        base = {t: {"total": 0, "ok": 0, "fail": 0} for t in C20_TABLES}
        base.update({"total": 0, "ok": 0, "fail": 0, "duracion": 0})
        return base

    def to_dict(self):
        """
        Devuelve el desglose por tabla más un consolidado.

        El consolidado usa OFC2CODE como referencia de la tarea: es la tabla por la
        que pasa cada número exactamente una vez, tanto en 'add' como en 'del'
        (SNPANAME y TOFCNAME operan sobre ladas/series deduplicadas, así que sus
        totales no son comparables con la cantidad de números del lote).
        """
        data = {
            t: {
                "total": getattr(self, f"{t}_total") or 0,
                "ok": getattr(self, f"{t}_ok") or 0,
                "fail": getattr(self, f"{t}_fail") or 0,
            } for t in C20_TABLES
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
        return {t: getattr(self, f"{t}_log") or "" for t in C20_TABLES}

class C20CommandLog(db.Model):
    """
    LOG DE COMANDOS (FULL FLOW): Almacena la interacción cruda de la sesión.
    """
    __tablename__ = 'c20_command_logs'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('c20_tasks.id'), nullable=False)
    raw_log = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "raw_log": self.raw_log,
            "fecha": self.fecha.isoformat() if self.fecha else None
        }


# El historial y el espejo viven en shared_models: son compartidos con Teams
# porque ambas secciones operan sobre el mismo nodo. Se reexportan aquí para no
# romper los imports existentes del módulo.
from app.modules.c20.shared_models import (  # noqa: E402,F401
    C20History, C20Snpaname, C20Tofcname, C20Ofc2code, C20Dnscrn,
)
