from __future__ import annotations

from uuid import UUID

import httpx

from app.domain.errores import DependenciaNoDisponible


class SuscripcionesHTTP:
    """Consulta la decisión de HU-13 en ms-suscripcion: GET /v1/suscripciones/{solicitud_id}."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def aceptada(self, solicitud_id: UUID) -> bool:
        try:
            respuesta = await self._http.get(f"/v1/suscripciones/{solicitud_id}")
        except httpx.HTTPError as exc:
            raise DependenciaNoDisponible("ms-suscripcion") from exc
        if respuesta.status_code == 404:
            return False
        if respuesta.status_code != 200:
            raise DependenciaNoDisponible("ms-suscripcion")
        return respuesta.json().get("decision") == "ACEPTADA"


class CobrosHTTP:
    """Consulta el cobro de HU-15 en ms-pagos: GET /v1/pagos/{pago_id}. Solo vale un cobro APROBADO
    de la misma oferta; un pago rechazado, inexistente o de otra oferta no habilita la emisión."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def exitoso(self, oferta_id: UUID, token_pago_confirmado: UUID) -> bool:
        try:
            respuesta = await self._http.get(f"/v1/pagos/{token_pago_confirmado}")
        except httpx.HTTPError as exc:
            raise DependenciaNoDisponible("ms-pagos") from exc
        if respuesta.status_code == 404:
            return False
        if respuesta.status_code != 200:
            raise DependenciaNoDisponible("ms-pagos")
        pago = respuesta.json()
        return pago.get("estado") == "APROBADO" and pago.get("oferta_id") == str(oferta_id)
