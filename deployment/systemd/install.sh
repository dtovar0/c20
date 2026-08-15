#!/usr/bin/env bash
#
# Instala las unidades systemd de Nexus C20.
# Requiere root:  sudo ./deployment/systemd/install.sh
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
UNIT_DIR="/etc/systemd/system"
UNITS=(nexus-web.service nexus-c20-worker.service nexus-psx5k-worker.service)

if [[ $EUID -ne 0 ]]; then
    echo "Este script necesita root. Ejecute: sudo $0" >&2
    exit 1
fi

echo "Proyecto: $PROJECT_DIR"

# Las unidades llevan rutas absolutas a /home/dtovar/bayblade/c20. Si el
# proyecto vive en otro sitio, se ajustan al vuelo durante la copia.
for unit in "${UNITS[@]}"; do
    src="$PROJECT_DIR/deployment/systemd/$unit"
    [[ -f "$src" ]] || { echo "No se encontró $src" >&2; exit 1; }
    sed "s|/home/dtovar/bayblade/c20|$PROJECT_DIR|g" "$src" > "$UNIT_DIR/$unit"
    echo "  instalado $unit"
done

# Comprobaciones previas: sin esto el servicio arranca y muere en bucle
[[ -f "$PROJECT_DIR/.env" ]] || echo "  AVISO: falta $PROJECT_DIR/.env"
[[ -x "$PROJECT_DIR/venv/bin/gunicorn" ]] || echo "  AVISO: falta venv/bin/gunicorn"
mkdir -p "$PROJECT_DIR/logs" "$PROJECT_DIR/uploads/c20" "$PROJECT_DIR/uploads/teams" "$PROJECT_DIR/uploads/psx5k"
chown -R "$(stat -c '%U:%G' "$PROJECT_DIR")" "$PROJECT_DIR/logs" "$PROJECT_DIR/uploads"

systemctl daemon-reload
echo
echo "Unidades instaladas. Para activarlas:"
echo "  systemctl enable --now nexus-web nexus-c20-worker nexus-psx5k-worker"
echo
echo "Estado y registro:"
echo "  systemctl status nexus-web"
echo "  journalctl -u nexus-c20-worker -f"
