# Despliegue de Authelia para Nexus

Este directorio contiene la infraestructura necesaria para habilitar Single Sign-On (SSO) en el proyecto Nexus.

## Instalación rápida
1. Asegúrate de tener **Docker** y **Docker Compose** instalados.
2. Edita `config/configuration.yml` y ajusta:
   - `jwt_secret`, `session.secret` y `storage.encryption_key`.
   - El dominio de tu servidor (`example.com`).
   - (Opcional) Configura la sección `ldap` si ya tienes el servidor listo.
3. Levanta los servicios:
   ```bash
   docker-compose up -d
   ```

## Integración con Nexus
Una vez que Authelia esté corriendo tras un Proxy Inverso (Nginx/Traefik), configura el archivo `.env` de Nexus:
- `AUTHELIA_ENABLED=true`
- `AUTHELIA_URL=https://tu-dominio-auth.com`

## Usuarios por defecto (Pruebas)
- Usuario: `admin`
- Password: `password`
