from __future__ import annotations

import logging

import httpx

from .token_servicio import token_de_servicio

logger = logging.getLogger(__name__)


class ClienteConsentimientoHTTP:
    """Adaptador real hacia ms-consentimiento (habeas data), construido
    contra el contrato ya coordinado con el otro equipo mientras ese
    servicio se desarrolla en paralelo (otra rama/worktree): no existe
    todavía un ms-consentimiento real contra el que probar esta llamada.

    GET /v1/consentimientos/{cliente_id}:
      - 200 {"vigente": true, ...}  -> hay habeas data vigente.
      - 200 {"vigente": false, ...} -> fue otorgado pero está revocado.
      - 404                          -> el contrato no distingue "nunca se
        otorgó" de "se otorgó y se revocó". Este adaptador trata ambos casos
        igual (False), porque el campo de salida `consentimiento` del
        cliente (ver casos_uso_clientes.py) tampoco distingue esos dos
        orígenes: en cualquiera de los dos no hay habeas data vigente hoy.

    Si el servicio no responde (timeout, conexión rechazada, 5xx) se
    DEGRADA a False en vez de propagar el error: el listado de clientes del
    back-office no puede caerse completo por un campo secundario de un
    cliente. Se deja constancia en el log como advertencia, no como error,
    porque es un comportamiento esperado mientras ms-consentimiento no esté
    desplegado.

    ms-consentimiento ya exige autenticación (rechaza llamadas sin token):
    se genera un token de servicio nuevo en cada llamada (dura 5 minutos,
    no se puede reusar de un arranque a otro de este proceso)."""

    def __init__(self, http: httpx.AsyncClient, secreto: str) -> None:
        self._http = http
        self._secreto = secreto

    async def vigente(self, cliente_id: str) -> bool:
        try:
            respuesta = await self._http.get(
                f"/v1/consentimientos/{cliente_id}",
                headers={"Authorization": f"Bearer {token_de_servicio(self._secreto, 'ms-identidad')}"},
            )
        except httpx.HTTPError:
            logger.warning("ms-consentimiento no disponible al consultar %s; se asume sin habeas data", cliente_id)
            return False

        if respuesta.status_code == 404:
            return False
        if respuesta.status_code >= 400:
            logger.warning(
                "ms-consentimiento respondió %s al consultar %s; se asume sin habeas data",
                respuesta.status_code,
                cliente_id,
            )
            return False

        try:
            return bool(respuesta.json().get("vigente", False))
        except ValueError:
            logger.warning("ms-consentimiento devolvió un cuerpo no JSON para %s; se asume sin habeas data", cliente_id)
            return False
