# Business Rules - Multi-Agent System

## Módulo: Core
### Regla: Arquitectura Modular
Todo el backend debe estar estructurado en Blueprints dentro de `app/modules/`.
### Impacto: Backend

## Módulo: UI/UX
### Regla: Estilos Basados en Tokens
Prohibido el uso de styles inline o selectores CSS arbitrarios fuera de Tailwind y el sistema de tokens.
### Impacto: Frontend

## Módulo: Notificaciones
### Regla: Persistencia de Plantillas
Las plantillas deben guardarse en la base de datos vinculadas a un slug único. Si no existen, el sistema debe cargar los predeterminados y ofrecer guardarlos.
### Ejemplo
Al seleccionar 'Inicio', se busca en la DB; si no está, se carga el default de seguridad y se notifica al usuario.
### Impacto
Backend + Base de Datos

## Módulo: PSX5K
### Regla: Registro de Operaciones
Todas las acciones de agregado/eliminado de tareas en el terminal PSX5K deben quedar registradas con su estado (Ejecutando, Programada, Terminada) y marcas de tiempo precisas para trazabilidad del proceso.
### Ejemplo
Al programar una eliminación de lote, se crea un registro con estado 'Programada'. Al finalizar, el motor actualiza a 'Terminada' y estampa la 'Fecha Fin'.
### Impacto
Operación PSX5K
