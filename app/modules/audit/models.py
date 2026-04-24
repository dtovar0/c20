from app import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    user = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=True)
    status = db.Column(db.String(20), default='info') # success, error, warning, info
    detail = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "time": self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "user": self.user,
            "action": self.action,
            "ip": self.ip_address,
            "status": self.status,
            "detail": self.detail
        }
