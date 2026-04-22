from app import db
from datetime import datetime

class PSX5KTask(db.Model):
    __tablename__ = 'psx5k_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False)
    tarea = db.Column(db.String(200), nullable=False)
    estado = db.Column(db.String(20), default='Programada')
    accion_tipo = db.Column(db.String(20), nullable=True)
    routing_label = db.Column(db.String(100), nullable=True)
    fecha_inicio = db.Column(db.DateTime, nullable=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    datos_tipo = db.Column(db.String(50), nullable=True)
    datos = db.Column(db.Text, nullable=True)
    force = db.Column(db.Boolean, default=False)
    
    # Vinculación lógica mediante ID compartido
    @property
    def resumen(self):
        return PSX5KDetail.query.get(self.id)

    def to_dict(self):
        res = self.resumen
        return {
            "id": self.id,
            "usuario": self.usuario,
            "tarea": self.tarea,
            "estado": self.estado,
            "accion_tipo": self.accion_tipo,
            "routing_label": self.routing_label,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "created_at": self.created_at.isoformat(),
            "datos_tipo": self.datos_tipo,
            "datos": self.datos,
            "resumen": res.to_dict() if res else {"total": 0, "ok": 0, "fail": 0}
        }

class PSX5KDetail(db.Model):
    __tablename__ = 'psx5k_details'
    
    id = db.Column(db.Integer, primary_key=True) # Corresponde al ID de la tarea
    total = db.Column(db.Integer, default=0)
    ok = db.Column(db.Integer, default=0)
    fail = db.Column(db.Integer, default=0)
    force_ok = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "total": self.total,
            "ok": self.ok,
            "fail": self.fail,
            "force_ok": self.force_ok
        }

class PSX5KHistory(db.Model):
    __tablename__ = 'psx5k_history'
    
    id = db.Column(db.Integer, primary_key=True) # ID único del registro histórico
    task_id = db.Column(db.Integer, nullable=False) # ID de la tarea que procesó el número
    usuario = db.Column(db.String(100), nullable=False)
    numero = db.Column(db.String(20), nullable=False)
    routing_label = db.Column(db.String(100), nullable=True)
    accion = db.Column(db.String(50), nullable=False)
    estado = db.Column(db.String(20), nullable=False) # OK, FAIL, DUP, etc.
    fecha = db.Column(db.DateTime, default=datetime.utcnow)

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
