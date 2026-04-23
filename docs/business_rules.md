# 📚 MOTOR DE REGLAS DE NEGOCIO - NEXUS

## Módulo: PSX5K Terminal

### Regla: Selección de Precisión
La selección de registros en la tabla PSX5K debe realizarse exclusivamente a través de la primera columna (checkbox). El clic en el resto de la fila no debe activar la selección para evitar errores operativos durante la visualización de datos de tareas.

### Ejemplo
El usuario hace clic en el Ticket #1234 para copiarlo; la fila no se selecciona. El usuario hace clic en el checkbox; la fila se marca y se habilitan las acciones de modificación.

### Impacto
Sistema de gestión de tareas PSX5K.

---

## Módulo: Autenticación / Usuarios

### Regla: Simetría de Acciones
Todos los botones de acción principal en las tablas administrativas (Modificar, Eliminar, Añadir) deben mantener un ancho fijo de 180px para garantizar un ritmo visual constante y profesional.

### Ejemplo
El botón "Añadir" tiene el mismo largo físico que "Modificar", independientemente de la longitud del texto.

### Impacto
Interfaz de administración de usuarios y roles.
