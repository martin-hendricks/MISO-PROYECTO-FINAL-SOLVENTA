from __future__ import annotations

from html import escape
from string import Template

# Un acento de color por tipo de notificación, para que el correo se distinga
# a simple vista (verde = buena noticia, ámbar = cambio, rojo = cancelación).
_COLOR_ACENTO = {
    "poliza_emitida": "#0f9d58",
    "poliza_renovada": "#0f9d58",
    "poliza_modificada": "#f4b400",
    "poliza_cancelada": "#d93025",
    "consentimiento_pendiente": "#4285f4",
}
_COLOR_POR_DEFECTO = "#1a73e8"

# Un único layout para todos los tipos: cabecera de marca, barra de acento del
# color de arriba, título y cuerpo. No hay botón de acción porque `destino` es
# una clave de enrutamiento interno de la app móvil (ver push_fcm.py), no una
# URL pública que este servicio pueda construir.
_PLANTILLA = Template(
    """<!doctype html>
<html lang="es">
  <body style="margin:0;padding:0;background:#f4f4f5;font-family:Arial,Helvetica,sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:24px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:8px;overflow:hidden;">
            <tr>
              <td style="background:#0b1f3a;padding:20px 24px;">
                <span style="color:#ffffff;font-size:18px;font-weight:bold;">Solventa</span>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 24px 8px 24px;border-top:4px solid $color;">
                <h1 style="margin:0 0 12px 0;color:#0b1f3a;font-size:20px;">$titulo</h1>
                <p style="margin:0;color:#333333;font-size:15px;line-height:1.5;">$cuerpo</p>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 24px 24px 24px;">
                <p style="margin:0;color:#8a8a8a;font-size:12px;">Este es un mensaje automático de Solventa, no respondas a este correo.</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""
)


def renderizar(tipo: str, titulo: str, cuerpo: str) -> str:
    """HTML del correo para `tipo`. Es la alternativa `Body.Html` que acompaña al
    `Body.Text` ya existente (ver email_ses.py): SES envía ambas partes y cada
    cliente de correo elige cuál renderizar. Un `tipo` sin acento propio usa el
    color por defecto en vez de fallar."""
    return _PLANTILLA.safe_substitute(
        color=_COLOR_ACENTO.get(tipo, _COLOR_POR_DEFECTO),
        titulo=escape(titulo),
        cuerpo=escape(cuerpo).replace("\n", "<br>"),
    )
