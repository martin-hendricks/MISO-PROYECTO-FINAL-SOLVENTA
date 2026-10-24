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


class CobroDeclarado:
    """Adaptador provisional mientras ms-pagos (HU-15) no existe: acepta la referencia del cobro
    exitoso que envía quien solicita la emisión. HU-15 debe reemplazarlo por un adaptador que
    consulte ms-pagos, sin tocar el caso de uso (puerto VerificadorCobro)."""

    async def exitoso(self, oferta_id: UUID, referencia_cobro: str) -> bool:
        return bool(referencia_cobro.strip())
