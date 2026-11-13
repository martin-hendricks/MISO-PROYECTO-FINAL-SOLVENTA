from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)


class ClientePerfilamientoHTTP:
    """Adaptador real hacia ms-perfilamiento: GET /v1/originaciones/clientes/
    {cliente_id}/pendiente. 200 con el cuerpo de la Originacion si hay una
    abierta (cerrada_en IS NULL); 404 si no hay ninguna pendiente.

    A diferencia de ms-consentimiento (todavía sin implementación real),
    ms-perfilamiento SÍ existe y responde este contrato hoy -- ver
    apps/backend/ms-perfilamiento/app/api/v1/rutas.py.

    Mismo criterio de degradación que ClienteConsentimientoHTTP: un timeout
    o una caída del servicio no debe tumbar el listado de clientes, se
    asume sin originación pendiente y se deja constancia en el log."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def tiene_originacion_pendiente(self, cliente_id: str) -> bool:
        try:
            respuesta = await self._http.get(f"/v1/originaciones/clientes/{cliente_id}/pendiente")
        except httpx.HTTPError:
            logger.warning("ms-perfilamiento no disponible al consultar %s; se asume sin originación pendiente", cliente_id)
            return False

        if respuesta.status_code == 404:
            return False
        if respuesta.status_code >= 400:
            logger.warning(
                "ms-perfilamiento respondió %s al consultar %s; se asume sin originación pendiente",
                respuesta.status_code,
                cliente_id,
            )
            return False

        try:
            return bool(respuesta.json().get("pendiente", True))
        except ValueError:
            logger.warning(
                "ms-perfilamiento devolvió un cuerpo no JSON para %s; se asume sin originación pendiente", cliente_id
            )
            return False
