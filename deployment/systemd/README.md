# Servicios systemd

Tres unidades: la web y un worker por nodo.

| Unidad | Proceso | Lock |
|---|---|---|
| `nexus-web` | Gunicorn, 3 workers, puerto 5000 | — |
| `nexus-c20-worker` | `bin/backend_c20.py` — atiende **C20 y Teams** | `c20_worker.pid` |
| `nexus-psx5k-worker` | `bin/backend_psx5k.py` | `psx5k_worker.pid` |

## Instalación

```bash
sudo ./deployment/systemd/install.sh
sudo systemctl enable --now nexus-web nexus-c20-worker nexus-psx5k-worker
```

El instalador ajusta las rutas si el proyecto no está en `/home/dtovar/bayblade/c20`.

## Operación

```bash
systemctl status nexus-c20-worker
journalctl -u nexus-c20-worker -f      # seguir el registro en vivo
systemctl restart nexus-web
```

## Por qué un solo worker para C20 y Teams

El nodo admite **una única conexión activa**, así que solo puede ejecutarse una
tarea a la vez sin importar de qué sección venga. Un único proceso decide qué
tarea toca en cada ciclo, lo que hace imposible el solape por construcción.

Levantar una segunda instancia de `nexus-c20-worker` no funcionaría —el lock lo
impide— pero tampoco tiene sentido: la segunda abortaría al arrancar.

PSX5K sí ataca un nodo distinto, por eso tiene su propio worker y su propio lock:
ambos pueden correr en paralelo.

## Antes de arrancar

1. **`.env` configurado**, en particular `C20_PASS` (vacío por defecto).
2. **Base de datos accesible**: las tablas se crean solas al arrancar la web
   (`db.create_all()`), pero solo las que no existan. Si el servidor ya tuvo una
   versión anterior de las tablas `c20_*` o `teams_*`, hay que borrarlas para que
   se regeneren con el esquema actual. No tocar las `psx5k_*`, que tienen datos.
3. **Permisos** sobre `uploads/` y `logs/` para el usuario del servicio.

## Parada

Los workers reciben `SIGTERM` y disponen de 60 s para cerrar la sesión con el
nodo antes de que systemd los mate. El lock se borra al salir; si el proceso
muere de golpe, el siguiente arranque detecta el lock huérfano (comprueba si el
PID sigue vivo) y lo limpia.

Una tarea interrumpida a media ejecución queda en estado `Ejecutando` y **bloquea
la cola** hasta que el watchdog la aborte, a los 90 minutos por defecto
(`C20_KILL_TASK_TIMEOUT`). Para liberarla antes, se pasa a `Pendiente` desde la
propia interfaz con la acción *Activar*.
