# 🏗️ ARQUITECTURA TÉCNICA - NEXUS

## 🧩 Patrón de Diseño
NEXUS utiliza una arquitectura modular basada en **Flask Blueprints**. Cada módulo es independiente y maneja su propia lógica de negocio, modelos de base de datos y rutas, permitiendo un escalado horizontal del código.

## 💾 Modelado de Datos (PSX5K)
El sistema utiliza un esquema **Master-Detail** para la gestión de tareas PSX:

1.  **PSX5KJob (Master)**: Contiene los metadatos globales de la operación (Usuario, Fecha, Tipo de Tarea, Archivo fuente/Datos).
2.  **PSX5KTask (Detail)**: Representa una unidad de ejecución. Si una tarea es masiva, se divide en chunks que el worker procesa individualmente.
3.  **PSX5KDetail**: Almacena las estadísticas de ejecución (Éxitos, Fallos, Duplicados).
4.  **PSX5KHistory**: Registro histórico detallado de cada número (ANI) procesado.
5.  **PSX5KCommandLog**: Captura el flujo raw de la terminal/consola durante la ejecución del comando.

## ⚙️ El Motor de Ejecución (Worker Daemon)
El archivo `backend_psx5k.py` actúa como un orquestador que se ejecuta continuamente en segundo plano.

### Ciclo de Vida de una Tarea:
1.  **Frontend**: El usuario sube un CSV o ingresa rangos; se crea un `Job` y sus correspondientes `Tasks`.
2.  **Worker (Watchdog)**:
    *   Verifica conectividad con el nodo PSX.
    *   Detecta tareas en estado `Pendiente` o `Programada`.
    *   Cambia estado a `Ejecutando`.
3.  **Ejecución**: Invoca `psx5k_cmd.py` para interactuar con la terminal del nodo.
4.  **Finalización**: Actualiza el estado a `Terminada` o `Error`, registra la auditoría y envía notificaciones por correo.

## 🔐 Seguridad y Auditoría
*   **LDAP Integration**: Permite la sincronización de usuarios corporativos mapeando atributos CN y Mail.
*   **AuditLog**: Cada interacción de escritura o cambio de configuración se registra en la tabla `audit_logs`, capturando Usuario, IP, Acción y Timestamp.
*   **Hygiene Routine**: El worker ejecuta una purga diaria de usuarios inactivos (>30 días) para mantener la higiene de la base de datos de identidades.

## 📧 Motor de Notificaciones
Centralizado en el módulo `notifications`, permite:
*   Configuración dinámica de SMTP.
*   Uso de **Slugs** (ej: `inicio`, `terminado`, `error`) para llamar a plantillas preconfiguradas.
*   Inyección de contexto dinámico (Variables Jinja2 en los correos).
