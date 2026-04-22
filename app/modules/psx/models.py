from app import db
from datetime import datetime

class PSX5K(db.Model):
    __tablename__ = 'psx5k'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(100), nullable=False) # Usuario que ejecuta la acción
    accion = db.Column(db.String(20), nullable=False)  # add/delete
    estado = db.Column(db.String(20), default='Programada')  # Ejecutando | Programada | Terminada
    fecha_inicio = db.Column(db.DateTime, nullable=True)
    fecha_fin = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    tipo = db.Column(db.String(20), nullable=True) # Manual | Archivo
    datos = db.Column(db.Text, nullable=True) # Información adicional en formato flexible (JSON/String)

    def to_dict(self):
        return {
            "id": self.id,
            "usuario": self.usuario,
            "accion": self.accion,
            "estado": self.estado,
            "tipo": self.tipo,
            "fecha_inicio": self.fecha_inicio.isoformat() if self.fecha_inicio else None,
            "fecha_fin": self.fecha_fin.isoformat() if self.fecha_fin else None,
            "created_at": self.created_at.isoformat(),
            "datos": self.datos
        }
