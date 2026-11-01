from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid5

import httpx

from app.domain.errores import DependenciaNoDisponible
from app.domain.modelos import EstadoPago, ResultadoPasarela

TOKEN_RECHAZO = "tok_rechazo"
_ESPACIO_STUB = UUID("5f0c8a52-7d4f-4f6e-9a57-3b1c2d0e9f11")


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


class PasarelaStub:
    """Simula la pasarela sin integrarse con un proveedor real (HU-15). Es determinista para poder
    probar ambos resultados: el token `tok_rechazo` se rechaza y cualquier otro se aprueba. La
    referencia externa se deriva de la clave, así un mismo cobro siempre tiene la misma referencia."""

    proveedor = "stub"

    async def cobrar(self, token_medio_pago: str, monto: Decimal, idempotency_key: str) -> ResultadoPasarela:
        estado = EstadoPago.RECHAZADO if token_medio_pago == TOKEN_RECHAZO else EstadoPago.APROBADO
        return ResultadoPasarela(
            estado=estado,
            proveedor=self.proveedor,
            referencia_externa=f"stub-{uuid5(_ESPACIO_STUB, idempotency_key)}",
        )
