# 🧠 NEXUS - UNIFIED SYSTEM TERMINAL

NEXUS es una plataforma de gestión centralizada diseñada para el monitoreo y administración de tareas operativas críticas, específicamente enfocada en el control de nodos **PSX5K** y la gestión de identidades/notificaciones.

## 🚀 Características Principales

*   **Gestión PSX5K**: Automatización de comandos (add/del) para números (ANIs) en nodos PSX.
*   **Monitoreo en Tiempo Real**: Dashboard administrativo con telemetría de tareas y logs de auditoría.
*   **Seguridad de Grado Empresarial**: Sistema de autenticación con soporte LDAP y control de acceso basado en roles (RBAC).
*   **Sistema de Notificaciones**: Motor de plantillas configurable para alertas por correo electrónico y notificaciones in-app.
*   **Auditoría Integral**: Registro detallado de cada acción realizada en el sistema.
*   **Worker Daemon**: Procesamiento asíncrono y persistente para tareas de larga duración.

## 🛠️ Stack Tecnológico

*   **Backend**: Python 3.x, Flask (Modular con Blueprints).
*   **Frontend**: Tailwind CSS, Vanilla JS, Design Tokens (Consistencia Visual).
*   **Base de Datos**: SQLAlchemy (Soporte para SQLite y MySQL).
*   **Worker**: Daemon de procesamiento asíncrono con sistema de bloqueo (lockfile).
*   **Entorno**: Soporte nativo para variables `.env`.

## 📂 Estructura del Proyecto

```text
/
├── app/                  # Núcleo de la aplicación Flask
│   ├── modules/          # Módulos independientes (Blueprints)
│   │   ├── auth/         # Autenticación y Usuarios
│   │   ├── psx/          # Gestión PSX5K
│   │   ├── notifications/# SMTP y Plantillas
│   │   ├── audit/        # Logs de Auditoría
│   │   └── settings/     # Configuración de Sistema
│   └── utils/            # Utilidades compartidas
├── static/               # Activos estáticos (CSS/JS/Design Tokens)
├── templates/            # Plantillas Jinja2
├── backend_psx5k.py      # Daemon Procesador de Tareas
├── psx5k_cmd.py          # Lógica de ejecución de comandos PSX
└── run.py                # Punto de entrada de la aplicación
```

## ⚙️ Configuración Rápida

1.  **Clonar y configurar entorno**:
    ```bash
    cp .env.example .env
    # Editar .env con tus credenciales
    ```
2.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Iniciar Aplicación**:
    ```bash
    python run.py
    ```
4.  **Iniciar Worker (Segundo Plano)**:
    ```bash
    nohup python backend_psx5k.py &
    ```

## 📚 Documentación Adicional

*   [Reglas de Negocio](docs/business_rules.md): Lineamientos operativos y de diseño.
*   [Arquitectura Técnica](docs/ARCHITECTURE.md): Detalles sobre el flujo de datos y base de datos.
*   [Guía de Estilos](UI_GUIDE.md): Design tokens y componentes reutilizables.
