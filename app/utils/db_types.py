"""
Tipos de columna portables entre MySQL y SQLite.
"""
from sqlalchemy import Text
from sqlalchemy.dialects.mysql import LONGTEXT

# Los logs crudos de sesión (`raw_log`) superan con holgura los 64 KB que
# admite un TEXT de MySQL: una carga masiva deja cientos de miles de
# caracteres de eco de terminal. LONGTEXT (4 GB) los absorbe sin recortar.
# En SQLite el TEXT no tiene tope práctico, así que allí basta el genérico.
LongText = Text().with_variant(LONGTEXT(), 'mysql')
