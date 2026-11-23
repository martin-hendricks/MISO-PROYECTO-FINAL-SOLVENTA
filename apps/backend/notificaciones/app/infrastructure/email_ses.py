from __future__ import annotations

import asyncio
import logging

from app.domain.errores import ServicioExternoNoDisponible

logger = logging.getLogger(__name__)


class EnviadorSES:
    """Envía correo con Amazon SES (API v2): texto plano siempre, HTML si se provee.

    Las credenciales salen del rol IRSA del pod. Importa boto3 de forma perezosa
    para que los tests no necesiten credenciales de AWS.
    """

    def __init__(self, region: str, remitente: str, configuration_set: str = "") -> None:
        self._region = region
        self._remitente = remitente
        self._configuration_set = configuration_set
        self._cliente = None

    def _sesv2(self):
        if self._cliente is None:
            import boto3

            self._cliente = boto3.client("sesv2", region_name=self._region)
        return self._cliente

    def _enviar(self, destinatario: str, asunto: str, cuerpo: str, cuerpo_html: str | None) -> str:
        from botocore.exceptions import BotoCoreError, ClientError

        cuerpo_mensaje = {"Text": {"Data": cuerpo, "Charset": "UTF-8"}}
        if cuerpo_html:
            cuerpo_mensaje["Html"] = {"Data": cuerpo_html, "Charset": "UTF-8"}

        argumentos = {
            "FromEmailAddress": self._remitente,
            "Destination": {"ToAddresses": [destinatario]},
            "Content": {
                "Simple": {
                    "Subject": {"Data": asunto, "Charset": "UTF-8"},
                    "Body": cuerpo_mensaje,
                }
            },
        }
        if self._configuration_set:
            argumentos["ConfigurationSetName"] = self._configuration_set
        try:
            return self._sesv2().send_email(**argumentos)["MessageId"]
        except (BotoCoreError, ClientError) as exc:
            logger.warning("ses_envio_fallido", extra={"error": type(exc).__name__})
            raise ServicioExternoNoDisponible("Amazon SES no pudo enviar el correo") from exc

    async def enviar(
        self, destinatario: str, asunto: str, cuerpo: str, cuerpo_html: str | None = None
    ) -> str:
        return await asyncio.to_thread(self._enviar, destinatario, asunto, cuerpo, cuerpo_html)
