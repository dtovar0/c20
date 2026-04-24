# 📚 MOTOR DE REGLAS DE NEGOCIO - NEXUS

## Módulo: PSX5K Terminal

### Regla: Selección de Precisión
La selección de registros en la tabla PSX5K debe realizarse exclusivamente a través de la primera columna (checkbox). El clic en el resto de la fila no debe activar la selección para evitar errores operativos durante la visualización de datos de tareas.

### Ejemplo
El usuario hace clic en el Ticket #1234 para copiarlo; la fila no se selecciona. El usuario hace clic en el checkbox; la fila se marca y se habilitan las acciones de modificación.

### Impacto
Sistema de gestión de tareas PSX5K.

---

## Módulo: Worker / Procesamiento Asíncrono

### Regla: Limpieza de Tareas Estancadas (Watchdog)
Cualquier tarea que permanezca en estado "Ejecutando" por más de 60 minutos será marcada automáticamente como "Error" por el worker. Se notificará al administrador sobre este timeout.

### Impacto
Estabilidad del motor de procesamiento y detección de cuellos de botella técnicos.

---

## Módulo: Seguridad / Higiene

### Regla: Purga de Inactividad
Las cuentas de usuario que no registren actividad durante un periodo de 30 días naturales serán eliminadas automáticamente del sistema para mantener la integridad y seguridad de la base de datos de identidades.

### Impacto
Gestión de identidades y cumplimiento de políticas de seguridad.

---

## Módulo: Infraestructura / Conectividad

### Regla: Validación Proactiva de Salud (Healthcheck)
El sistema debe validar la conectividad con el nodo PSX antes de iniciar cualquier tarea operativa. Si el nodo se encuentra offline, la tarea se pospondrá 60 segundos y se generará una alerta crítica (in-app y email).


## Módulo: Autenticación / Usuarios

### Regla: Simetría de Acciones
Todos los botones de acción principal en las tablas administrativas (Modificar, Eliminar, Añadir) deben mantener un ancho fijo de 180px para garantizar un ritmo visual constante y profesional.

### Ejemplo
El botón "Añadir" tiene el mismo largo físico que "Modificar", independientemente de la longitud del texto.

### Impacto
Interfaz de administración de usuarios y roles.
