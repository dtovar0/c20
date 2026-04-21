from app import db
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='usuario') # administrador, usuario
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

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
