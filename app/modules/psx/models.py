from app import db
import datetime

class PSX5KJob(db.Model):
    """
    TABLA MAESTRA (HEADER): Contiene la definición global de la carga.
    """
    __tablename__ = 'psx5k_jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False)
    tarea = db.Column(db.String(50)) # add / delete
    accion_tipo = db.Column(db.String(50)) # bulk / etc
    datos_tipo = db.Column(db.String(50)) # Archivo / Manual
    routing_label = db.Column(db.String(100))
    archivo_origen = db.Column(db.String(255))
    run_force = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.now)
    
    # Relación con sus fragmentos (chunks)
    tasks = db.relationship('PSX5KTask', backref='job', lazy=True, cascade="all, delete-orphan")

class PSX5KTask(db.Model):
    """
    TABLA DE EJECUCIÓN (CHUNKS): Uno por cada 200 registros.
    """
    __tablename__ = 'psx5k_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('psx5k_jobs.id'), nullable=False)
    
    chunk_index = db.Column(db.Integer, default=1)
    chunk_total = db.Column(db.Integer, default=1)
    
    datos = db.Column(db.Text) # Almacena los números (se limpia al terminar)
    estado = db.Column(db.String(50), default='Pendiente')
    
    fecha_inicio = db.Column(db.DateTime)
    fecha_fin = db.Column(db.DateTime)
    
    # Relación de reintento (para el sistema de complementarias)
    parent_id = db.Column(db.Integer, db.ForeignKey('psx5k_tasks.id'), nullable=True)
    tipo = db.Column(db.String(20), default='normal') 

    @property
    def resumen(self):
        return PSX5KDetail.query.get(self.id)

    def to_dict(self):
        job = self.job
        res = self.resumen
        return {
            "id": self.id,
            "job_id": self.job_id,
            "usuario": job.usuario,
            "tarea": job.tarea,
            "estado": self.estado,
            "accion_tipo": job.accion_tipo,
            "routing_label": job.routing_label,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "created_at": job.created_at.isoformat(),
            "datos_tipo": job.datos_tipo,
            "archivo_origen": job.archivo_origen,
            "chunk_index": self.chunk_index,
            "chunk_total": self.chunk_total,
            "resumen": res.to_dict() if res else {"total": 0, "ok": 0, "fail": 0}
        }

class PSX5KDetail(db.Model):
    __tablename__ = 'psx5k_details'
    id = db.Column(db.Integer, primary_key=True)
    total = db.Column(db.Integer, default=0)
    ok = db.Column(db.Integer, default=0)
    fail = db.Column(db.Integer, default=0)
    force_ok = db.Column(db.Integer, default=0)
    dup = db.Column(db.Integer, default=0)
    del_ = db.Column(db.Integer, name='del', default=0)
    delcheck = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "total": self.total,
            "ok": self.ok,
            "fail": self.fail,
            "force_ok": self.force_ok,
            "dup": self.dup,
            "del": self.del_,
            "delcheck": self.delcheck
        }

class PSX5KHistory(db.Model):
    __tablename__ = 'psx5k_history'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('psx5k_tasks.id'), nullable=False)
    usuario = db.Column(db.String(100))
    numero = db.Column(db.String(20))
    routing_label = db.Column(db.String(100))
    accion = db.Column(db.String(50))
    estado = db.Column(db.String(50))
    fecha = db.Column(db.DateTime, default=datetime.datetime.now)
    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "usuario": self.usuario,
            "numero": self.numero,
            "routing_label": self.routing_label,
            "accion": self.accion,
            "estado": self.estado,
            "fecha": self.fecha.isoformat() if self.fecha else None
        }

class PSX5KCommandLog(db.Model):
    """
    LOG DE COMANDOS (FULL FLOW): Almacena la interacción cruda de pexpect.
    """
    __tablename__ = 'psx5k_command_logs'
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('psx5k_tasks.id'), nullable=False)
    raw_log = db.Column(db.Text)
    fecha = db.Column(db.DateTime, default=datetime.datetime.now)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "raw_log": self.raw_log,
            "fecha": self.fecha.isoformat() if self.fecha else None
        }
