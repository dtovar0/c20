from app import db
from datetime import datetime

class AuthConfig(db.Model):
    __tablename__ = 'auth_config'
    
    id = db.Column(db.Integer, primary_key=True)
    ldap_host = db.Column(db.String(100), nullable=True)
    ldap_port = db.Column(db.Integer, default=389)
    ldap_ssl = db.Column(db.Boolean, default=False)
    ldap_base_dn = db.Column(db.String(200), nullable=True)
    ldap_user = db.Column(db.String(100), nullable=True)
    ldap_pass = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "ldap_host": self.ldap_host,
            "ldap_port": self.ldap_port,
            "ldap_ssl": self.ldap_ssl,
            "ldap_base_dn": self.ldap_base_dn,
            "ldap_user": self.ldap_user
        }
