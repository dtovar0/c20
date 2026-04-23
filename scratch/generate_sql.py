
import sys
import os
from sqlalchemy import create_mock_engine

# Agregar el directorio raíz al path para importar la app
sys.path.append(os.path.abspath(os.curdir))

from app import db
from app.modules.auth.models import User, AuthConfig
from app.modules.audit.models import AuditLog
from app.modules.psx.models import PSX5KJob, PSX5KTask, PSX5KDetail, PSX5KHistory

def dump_sql(sql, *multiparams, **params):
    print(sql.compile(dialect=engine.dialect))

# Simulamos un motor de MySQL para obtener el SQL exacto
engine = create_mock_engine("mysql://", dump_sql)

print("-- === NEXUS ADMIN SYSTEM === --")
print("-- Database Structure Dump --")
print("-- Generated via SQLAlchemy Reflector --\n")
print("SET FOREIGN_KEY_CHECKS = 0;\n")

# Extraer el DDL de todas las tablas registradas en el metadata de SQLAlchemy
from sqlalchemy.schema import CreateTable
for table in db.metadata.sorted_tables:
    print(str(CreateTable(table).compile(dialect=engine.dialect)) + ";\n")

print("SET FOREIGN_KEY_CHECKS = 1;")
