from app import db
from datetime import datetime

class PSX5KTask(db.Model):
    __tablename__ = 'psx5k_tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False)
    accion = db.Column(db.String(20), nullable=False)      # add/delete
    estado = db.Column(db.String(20), default='Programada')  # Ejecutando | Programada | Terminada | Pendiente
    accion_tipo = db.Column(db.String(20), nullable=True)  # Manual | Archivo
    routing_label = db.Column(db.String(100), nullable=True) # Etiqueta de ruta
    fecha_inicio = db.Column(db.DateTime, nullable=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    datos_tipo = db.Column(db.String(50), nullable=True)   # Tipo de datos contenidos
    datos = db.Column(db.Text, nullable=True)              # Información adicional/Nota
    
    # Relación 1:1 con detalles de contadores
    detalle = db.relationship('PSX5KDetail', backref='task', uselist=False, lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "usuario": self.usuario,
            "accion": self.accion,
            "estado": self.estado,
            "accion_tipo": self.accion_tipo,
            "routing_label": self.routing_label,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "created_at": self.created_at.isoformat(),
            "datos_tipo": self.datos_tipo,
            "datos": self.datos,
            "resumen": self.detalle.to_dict() if self.detalle else {"total": 0, "ok": 0, "fail": 0}
        }

class PSX5KDetail(db.Model):
    __tablename__ = 'psx5k_details'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('psx5k_tasks.id'), nullable=False)
    total = db.Column(db.Integer, default=0)
    ok = db.Column(db.Integer, default=0)
    fail = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            "total": self.total,
            "ok": self.ok,
            "fail": self.fail
        }
