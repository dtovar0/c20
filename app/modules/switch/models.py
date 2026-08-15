"""
Modelos compartidos entre las secciones que operan sobre el mismo switch (C20 y
Teams).

Ambas secciones atacan el mismo nodo y las mismas tablas del conmutador, así que
el estado del switch y el rastro de cada número son únicos: no tiene sentido que
cada sección lleve su propia copia. Lo que sí es privado de cada una son la cola
de trabajos, las tareas y los contadores de ejecución.
"""
from app import db
import datetime

# Tablas del switch que produce cada ejecución, en orden jerárquico
# (lada -> serie -> número). Las dos primeras solo intervienen en 'add':
# una baja no retira ladas ni series.
SWITCH_TABLES = ('snpaname', 'tofcname', 'ofc2code', 'dnscrn')
SWITCH_DEL_TABLES = ('ofc2code', 'dnscrn')

# Secciones registradas. El sistema legado tenía además WSE, retirada tras la
# migración del C20 al PSX-S5K.
SECCIONES = ('c20', 'teams')


class SwitchHistory(db.Model):
    """
    HISTORIAL COMPARTIDO: rastro de todo lo que se ha intentado sobre cada
    número, venga de la sección que venga.

    A diferencia del espejo (que solo dice qué está vivo ahora), aquí se acumula
    una fila por cada intento —altas, bajas, aplicadas o no— para poder responder
    qué cambios tuvo un número a lo largo del tiempo.

    Tabla única con columna `seccion` en vez de una por sección (el sistema
    legado tenía history / history_wse / history_teams, aunque sus crons
    escribían todos en la primera). Así la vista individual es un filtro y la
    combinada es la tabla entera, sin duplicar filas ni resolver uniones.

    task_id no lleva FK: apunta a la tarea de la sección indicada en `seccion`,
    que vive en una tabla distinta según el caso (c20_tasks, teams_tasks).
    """
    __tablename__ = 'switch_history'
    id = db.Column(db.Integer, primary_key=True)
    seccion = db.Column(db.String(10), nullable=False, index=True)
    task_id = db.Column(db.Integer, nullable=False, index=True)
    usuario = db.Column(db.String(100), index=True)
    numero = db.Column(db.String(20), index=True)
    # Parámetro propio de la sección: zona en C20, prefijo en Teams
    parametro = db.Column(db.String(10))
    accion = db.Column(db.String(50))   # add / del
    estado = db.Column(db.String(50))   # OK (aplicado) / FAIL (sin aplicar) / ERROR
    fecha = db.Column(db.DateTime, default=datetime.datetime.now, index=True)

    __table_args__ = (
        # Trazabilidad de un número en orden cronológico, atravesando secciones
        db.Index('ix_switch_history_numero_fecha', 'numero', 'fecha'),
        # Recuperación del detalle de una tarea concreta
        db.Index('ix_switch_history_seccion_task', 'seccion', 'task_id'),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "seccion": self.seccion,
            "task_id": self.task_id,
            "usuario": self.usuario,
            "numero": self.numero,
            "parametro": self.parametro,
            "accion": self.accion,
            "estado": self.estado,
            "fecha": self.fecha.isoformat() if self.fecha else None
        }


# --- ESPEJO LOCAL DEL NODO ---
# Estas cuatro tablas reflejan QUÉ ESTÁ DADO DE ALTA ahora mismo en el switch:
# una fila por registro vivo, no un historial. La clave primaria garantiza que
# una lada, una serie o un número no puedan repetirse.
#
# No llevan columna 'accion': una fila presente significa "alta"; una baja se
# representa eliminando la fila. El rastro temporal vive en switch_history.
#
# Son compartidas porque el estado del switch es uno solo: un número dado de
# alta desde C20 ya existe para Teams, y viceversa.

class SwitchSnpaname(db.Model):
    """
    ESPEJO: ladas dadas de alta en el switch (tabla SNPANAME del nodo).
    Se consulta antes de intentar el alta para no repetir trabajo.
    La lada es varchar: '81' y '618' conviven, y nunca debe convertirse a entero
    (perdería ceros a la izquierda).
    """
    __tablename__ = 'switch_snpaname'
    lada = db.Column(db.String(3), primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.datetime.now, index=True)
    usuario = db.Column(db.String(50), index=True)
    seccion = db.Column(db.String(10), index=True)  # quién la dio de alta


class SwitchTofcname(db.Model):
    """ESPEJO: series dadas de alta en el switch (tabla TOFCNAME del nodo)."""
    __tablename__ = 'switch_tofcname'
    lada = db.Column(db.String(3), primary_key=True)
    serie = db.Column(db.String(4), primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.datetime.now, index=True)
    usuario = db.Column(db.String(50), index=True)
    seccion = db.Column(db.String(10), index=True)


class SwitchOfc2code(db.Model):
    """
    ESPEJO: números dados de alta en OFC2CODE.

    Se mantiene separada de DNSCRN pese a llevar los mismos números: si un alta
    se aplica en una tabla y falla en la otra, el espejo debe poder representar
    esa inconsistencia en vez de ocultarla.
    """
    __tablename__ = 'switch_ofc2code'
    numero = db.Column(db.String(10), primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.datetime.now, index=True)
    usuario = db.Column(db.String(50), index=True)
    seccion = db.Column(db.String(10), index=True)


class SwitchDnscrn(db.Model):
    """ESPEJO: números dados de alta en DNSCRN."""
    __tablename__ = 'switch_dnscrn'
    numero = db.Column(db.String(10), primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.datetime.now, index=True)
    usuario = db.Column(db.String(50), index=True)
    seccion = db.Column(db.String(10), index=True)


def make_detail_columns(prefix_table):
    """
    Genera las columnas de contadores de una tabla del switch.

    Cada sección guarda un juego total/ok/fail/log por tabla, igual que la tabla
    `daemon` del sistema legado: las cuatro tablas se procesan por separado y
    cada una produce su propio veredicto.
    """
    return {
        f"{prefix_table}_total": db.Column(db.Integer, default=0),
        f"{prefix_table}_ok": db.Column(db.Integer, default=0),
        f"{prefix_table}_fail": db.Column(db.Integer, default=0),
        f"{prefix_table}_log": db.Column(db.Text),
    }
