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
    datos = db.Column(db.Text, nullable=True)              # Información adicional/Nota (Legacy o metadata)
    
    # Relación con detalles
    detalles = db.relationship('PSX5KDetail', backref='task', lazy=True, cascade="all, delete-orphan")

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
            "total_items": len(self.detalles)
        }

class PSX5KDetail(db.Model):
    __tablename__ = 'psx5k_details'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('psx5k_tasks.id'), nullable=False)
    item_value = db.Column(db.String(255), nullable=False) # El número, nodo o dato específico
    item_status = db.Column(db.String(20), default='Pendiente') # Pendiente | Procesado | Error
    error_msg = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "value": self.item_value,
            "status": self.item_status,
            "error": self.error_msg
        }
