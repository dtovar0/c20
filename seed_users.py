from app import create_app, db
from app.modules.auth.models import User
import sys

def seed_users():
    app = create_app()
    with app.app_context():
        print("🌱 Iniciando sembrado de usuarios profesionales...")
        
        # Definición de datos profesionales
        demo_users = [
            { 'username': 'admin', 'name': 'Administrador Principal', 'role': 'admin', 'active': True },
            { 'username': 'dtovar', 'name': 'Daniel Tovar', 'role': 'admin', 'active': True },
            { 'username': 'schen', 'name': 'Sarah Chen', 'role': 'user', 'active': True },
            { 'username': 'mrosso', 'name': 'Marco Rosso', 'role': 'user', 'active': True },
            { 'username': 'anovak', 'name': 'Alex Novak', 'role': 'Audit Compliance', 'active': False },
            { 'username': 'engine', 'name': 'Service Engine', 'role': 'System', 'active': True },
            { 'username': 'auditor', 'name': 'External Auditor', 'role': 'Guest', 'active': False }
        ]

        for data in demo_users:
            # Verificar si ya existe para evitar duplicados
            existing = User.query.filter_by(username=data['username']).first()
            if not existing:
                user = User(
                    username=data['username'],
                    nombre=data['name'],
                    role=data['role'],
                    is_active=data['active']
                )
                user.set_password('Nexus2024!')
                db.session.add(user)
                print(f"✅ Usuario creado: {data['name']} ({data['role']})")
            else:
                print(f"⚠️ El usuario {data['name']} ya existe. Omitiendo.")

        try:
            db.session.commit()
            print("\n✨ Sembrado completado con éxito.")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error durante el sembrado: {str(e)}")

if __name__ == "__main__":
    seed_users()
