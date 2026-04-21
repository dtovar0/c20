from app import db
from datetime import datetime

class SMTPConfig(db.Model):
    __tablename__ = 'smtp_config'
    
    id = db.Column(db.Integer, primary_key=True)
    server = db.Column(db.String(100), default='smtp.gmail.com')
    port = db.Column(db.Integer, default=587)
    encryption = db.Column(db.String(20), default='starttls')
    auth_enabled = db.Column(db.Boolean, default=True)
    user = db.Column(db.String(100), nullable=True)
    password = db.Column(db.String(100), nullable=True) # Should be encrypted in production
    sender_name = db.Column(db.String(100), default='Nexus System')
    sender_email = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "server": self.server,
            "port": self.port,
            "encryption": self.encryption,
            "auth_enabled": self.auth_enabled,
            "user": self.user,
            "sender_name": self.sender_name,
            "sender_email": self.sender_email
        }
