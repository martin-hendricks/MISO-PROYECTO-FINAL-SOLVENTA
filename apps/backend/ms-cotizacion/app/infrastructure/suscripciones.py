from __future__ import annotations

from decimal import Decimal
from uuid import UUID

import httpx

from app.domain.errores import DependenciaNoDisponible
from app.ports.suscripcion import DecisionSuscripcion

from .token_servicio import token_de_servicio


class SuscripcionesHTTP:
    """Encadena la decisión de HU-13 en ms-suscripcion: POST /v1/suscripciones.
    ms-suscripcion exige autenticación: token de servicio nuevo en cada llamada."""

    def __init__(self, http: httpx.AsyncClient, secreto: str) -> None:
        self._http = http
        self._secreto = secreto

    async def evaluar(self, solicitud_id: UUID, perfil_id: UUID, score: Decimal) -> DecisionSuscripcion:
        cuerpo = {"solicitud_id": str(solicitud_id), "perfil_id": str(perfil_id), "score": str(score)}
        try:
            respuesta = await self._http.post(
                "/v1/suscripciones",
                json=cuerpo,
                headers={"Authorization": f"Bearer {token_de_servicio(self._secreto, 'ms-cotizacion')}"},
            )
        except httpx.HTTPError as exc:
            raise DependenciaNoDisponible("ms-suscripcion") from exc
        if respuesta.status_code not in (200, 201):
            raise DependenciaNoDisponible("ms-suscripcion")
        datos = respuesta.json()
        return DecisionSuscripcion(
            suscripcion_id=UUID(datos["suscripcion_id"]), decision=datos["decision"], motivo=datos["motivo"]
        )
