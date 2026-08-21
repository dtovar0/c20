"""
Resumen operativo de una tarea, en HTML, para el correo de cierre.

Replica lo que la vista de detalle muestra en 'Resumen Operativo': los datos de
la operación, los contadores por tabla y la eficiencia. El correo se arma aquí y
no con placeholders de plantilla porque el contenido es una tabla de cifras de
tamaño variable —cuatro tablas en un alta, dos en una baja— que no se puede
expresar con sustituciones de texto.

Restricciones de correo que explican el marcado:
  - Layout con <table>, no flex ni grid: Outlook los ignora.
  - Estilos inline en cada celda: los clientes descartan <style> del <head>.
  - Sin imágenes ni fuentes externas: se bloquean por defecto.
  - La barra de eficiencia es una celda con fondo y ancho en %, no un <div>.
"""

# Mismos umbrales y colores que la vista de detalle, para que el correo y la
# pantalla no cuenten cosas distintas.
_UMBRALES = ((98, '#10b981'), (80, '#0ea5e9'), (50, '#f59e0b'), (0, '#f43f5e'))

# Unidad de cada tabla, como en la vista. El orden es el de la jerarquía del
# nodo: lada -> serie -> número.
_TABLAS = (
    ('SNPANAME', 'Ladas'),
    ('TOFCNAME', 'Series'),
    ('OFC2CODE', 'Números'),
    ('DNSCRN', 'Números'),
)


def _color_eficiencia(pct):
    for minimo, color in _UMBRALES:
        if pct >= minimo:
            return color
    return _UMBRALES[-1][1]


def _fmt_duracion(segundos):
    """Duración legible. La vista redondea a minutos; aquí se conserva el detalle."""
    try:
        segundos = int(segundos or 0)
    except (TypeError, ValueError):
        return '-'
    if segundos < 60:
        return f"{segundos}s"
    minutos, resto = divmod(segundos, 60)
    return f"{minutos}m {resto}s" if resto else f"{minutos}m"


def _fila_meta(etiqueta, valor, resaltado=False):
    color = '#10b981' if resaltado else '#1a1a1a'
    peso = '700' if resaltado else '600'
    return (
        '<tr>'
        f'<td style="padding:8px 0;font-size:11px;color:#8a8f98;'
        'text-transform:uppercase;letter-spacing:1px;font-weight:700;">'
        f'{etiqueta}</td>'
        f'<td style="padding:8px 0;font-size:12px;color:{color};'
        f'font-weight:{peso};text-align:right;font-family:monospace;">'
        f'{valor}</td>'
        '</tr>'
    )


def _tarjeta_tabla(nombre, unidad, total, ok, fail):
    """
    Una tabla del nodo con sus tres cifras.

    Las que no participaron (una baja no toca SNPANAME ni TOFCNAME) se omiten en
    lugar de mostrarse en cero: en el correo no hay tooltip que explique el
    atenuado que sí usa la vista, y un 0 sin contexto se lee como un fallo.
    """
    if not total:
        return ''
    return (
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        'style="border:1px solid #e2e8f0;border-radius:10px;margin-bottom:10px;'
        'background:#fbfcfd;">'
        '<tr><td style="padding:14px 16px;">'
        f'<div style="font-size:11px;font-weight:800;color:#6366f1;'
        f'letter-spacing:2px;">{nombre}'
        f'<span style="float:right;color:#b0b5bd;font-size:10px;'
        f'letter-spacing:1px;">{unidad}</span></div>'
        '<table role="presentation" cellpadding="0" cellspacing="0" '
        'style="margin-top:10px;width:100%;">'
        '<tr>'
        '<td style="font-size:10px;color:#10b981;font-weight:700;'
        'letter-spacing:1px;padding-right:18px;">APLICADO</td>'
        '<td style="font-size:10px;color:#f59e0b;font-weight:700;'
        'letter-spacing:1px;padding-right:18px;">SIN APLICAR</td>'
        '<td style="font-size:10px;color:#b0b5bd;font-weight:700;'
        'letter-spacing:1px;text-align:right;">TOTAL</td>'
        '</tr>'
        '<tr>'
        f'<td style="font-size:22px;font-weight:800;color:#10b981;'
        f'padding-right:18px;">{ok or 0}</td>'
        f'<td style="font-size:22px;font-weight:800;color:#f59e0b;'
        f'padding-right:18px;">{fail or 0}</td>'
        f'<td style="font-size:16px;font-weight:800;color:#8a8f98;'
        f'text-align:right;">{total or 0}</td>'
        '</tr>'
        '</table>'
        '</td></tr></table>'
    )


def build_resumen_html(*, seccion, task_id, usuario, operacion, estado,
                       origen, secuencia, hora_inicio, hora_fin, duracion,
                       parametro, parametro_label, contadores, incidencias,
                       url=None):
    """
    Arma el resumen operativo.

    contadores: dict {'ofc2code': {'total': n, 'ok': n, 'fail': n}, ...}
    parametro:  zona (C20) o prefijo (Teams). None en una baja, que no lo usa;
                en ese caso la fila se omite en vez de mostrar un valor inerte.
    """
    es_baja = str(operacion).strip().lower() in ('del', 'delete')
    con_errores = bool(incidencias) and incidencias != 'Ninguna'

    ref = contadores.get('ofc2code', {}) or {}
    total_ref = ref.get('total', 0) or 0
    ok_ref = ref.get('ok', 0) or 0
    pct = round(ok_ref / total_ref * 100, 1) if total_ref else 0.0
    color_pct = _color_eficiencia(pct)

    color_estado = '#f43f5e' if con_errores else '#10b981'

    filas_meta = [
        _fila_meta('Operador', usuario),
        _fila_meta('Acción', 'BAJA (ELIMINAR)' if es_baja else 'ALTA (AGREGAR)'),
        _fila_meta('Origen de datos', origen or 'Ingreso Manual'),
        _fila_meta('Secuencia de carga', secuencia),
    ]
    # La zona/prefijo solo interviene en el alta.
    if not es_baja and parametro not in (None, '', '-'):
        filas_meta.append(_fila_meta(parametro_label, parametro))
    filas_meta += [
        _fila_meta('Inicio de ejecución', hora_inicio or '--:--:--'),
        _fila_meta('Fin de ejecución', hora_fin or '--:--:--'),
        _fila_meta('Duración', _fmt_duracion(duracion), resaltado=True),
    ]

    tarjetas = ''.join(
        _tarjeta_tabla(nombre, unidad,
                       (contadores.get(nombre.lower(), {}) or {}).get('total', 0),
                       (contadores.get(nombre.lower(), {}) or {}).get('ok', 0),
                       (contadores.get(nombre.lower(), {}) or {}).get('fail', 0))
        for nombre, unidad in _TABLAS
    )

    bloque_incidencias = ''
    if con_errores:
        bloque_incidencias = (
            '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            'style="margin-top:18px;border:1px solid #fecaca;border-radius:10px;'
            'background:#fef2f2;">'
            '<tr><td style="padding:14px 16px;">'
            '<div style="font-size:10px;font-weight:800;color:#f43f5e;'
            'letter-spacing:2px;margin-bottom:6px;">INCIDENCIAS</div>'
            f'<div style="font-size:12px;color:#7f1d1d;line-height:1.6;">'
            f'{incidencias}</div>'
            '</td></tr></table>'
        )

    boton = ''
    if url:
        boton = (
            f'<table role="presentation" cellpadding="0" cellspacing="0" '
            f'style="margin:22px auto 0;"><tr><td '
            f'style="background:#6366f1;border-radius:8px;">'
            f'<a href="{url}" style="display:inline-block;padding:12px 28px;'
            f'font-size:12px;font-weight:800;color:#ffffff;text-decoration:none;'
            f'letter-spacing:1px;">VER DETALLE COMPLETO</a>'
            f'</td></tr></table>'
        )

    return f"""<!DOCTYPE html>
<html><body style="margin:0;padding:0;background:#f1f5f9;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:#f1f5f9;padding:24px 12px;">
<tr><td align="center">
<table role="presentation" width="600" cellpadding="0" cellspacing="0"
       style="max-width:600px;background:#ffffff;border-radius:14px;
              overflow:hidden;font-family:Helvetica,Arial,sans-serif;
              box-shadow:0 1px 3px rgba(0,0,0,0.08);">

  <tr><td style="padding:24px 28px;border-bottom:1px solid #e2e8f0;">
    <div style="font-size:17px;font-weight:800;color:#1a1a1a;
                letter-spacing:-0.4px;">Resumen Operativo</div>
    <div style="font-size:11px;font-weight:700;color:#8a8f98;
                letter-spacing:1.5px;margin-top:3px;">
      {seccion.upper()} · TAREA #{task_id}
    </div>
    <div style="margin-top:12px;">
      <span style="display:inline-block;padding:5px 12px;border-radius:20px;
                   background:{color_estado}1a;color:{color_estado};
                   font-size:10px;font-weight:800;letter-spacing:1px;">
        ● {estado.upper()}
      </span>
    </div>
  </td></tr>

  <tr><td style="padding:22px 28px 8px;">
    <div style="font-size:10px;font-weight:800;color:#b0b5bd;
                letter-spacing:2px;margin-bottom:10px;">
      DETALLES DE OPERACIÓN
    </div>
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
      {''.join(filas_meta)}
    </table>
  </td></tr>

  <tr><td style="padding:18px 28px 4px;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="background:#f8fafc;border-radius:10px;">
      <tr><td style="padding:18px 20px;">
        <div style="font-size:10px;font-weight:800;color:#b0b5bd;
                    letter-spacing:2px;">TOTAL PROCESADO</div>
        <div style="margin-top:6px;">
          <span style="font-size:34px;font-weight:800;color:#1a1a1a;">{total_ref}</span>
          <span style="font-size:10px;font-weight:700;color:#b0b5bd;
                       letter-spacing:1.5px;margin-left:6px;">REGISTROS</span>
        </div>
      </td></tr>
    </table>
  </td></tr>

  <tr><td style="padding:14px 28px 0;">
    <div style="font-size:10px;font-weight:800;color:#b0b5bd;
                letter-spacing:2px;margin-bottom:10px;">
      TELEMETRÍA POR TABLA
    </div>
    {tarjetas}
  </td></tr>

  <tr><td style="padding:6px 28px 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
           style="border:1px solid #e2e8f0;border-radius:10px;">
      <tr><td style="padding:18px 20px;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="font-size:10px;font-weight:800;color:#b0b5bd;
                       letter-spacing:2px;">ÍNDICE DE CONFIABILIDAD</td>
            <td style="text-align:right;font-size:26px;font-weight:800;
                       color:{color_pct};">{pct}%</td>
          </tr>
          <tr><td colspan="2" style="font-size:14px;font-weight:800;
                   color:#1a1a1a;padding-top:2px;">Eficiencia Procedimental</td></tr>
        </table>
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0"
               style="margin-top:12px;background:#eef1f5;border-radius:6px;">
          <tr><td style="padding:0;">
            <table role="presentation" width="{max(pct, 1)}%" cellpadding="0"
                   cellspacing="0"><tr>
              <td style="background:{color_pct};height:8px;
                         border-radius:6px;font-size:0;line-height:0;">&nbsp;</td>
            </tr></table>
          </td></tr>
        </table>
        <div style="font-size:10px;color:#b0b5bd;margin-top:10px;
                    letter-spacing:0.5px;">
          Calculado sobre OFC2CODE, la tabla por la que pasa cada número una vez.
          «Sin aplicar» no es un error: el registro no estaba en el estado
          esperado{' (no existía)' if es_baja else ' (ya existía)'}.
        </div>
      </td></tr>
    </table>
    {bloque_incidencias}
    {boton}
  </td></tr>

  <tr><td style="padding:22px 28px;text-align:center;">
    <div style="font-size:10px;color:#b0b5bd;letter-spacing:1px;">
      SERVICIO NEXUS CORE · MENSAJE AUTOMÁTICO
    </div>
  </td></tr>

</table>
</td></tr></table>
</body></html>"""
