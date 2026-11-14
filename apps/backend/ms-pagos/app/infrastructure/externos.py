from __future__ import annotations

import asyncio
from decimal import Decimal
from uuid import UUID, uuid5

import httpx

from app.domain.errores import DependenciaNoDisponible
from app.domain.modelos import EstadoPago, ResultadoPasarela

from .token_servicio import token_de_servicio

TOKEN_RECHAZO = "tok_rechazo"
_ESPACIO_STUB = UUID("5f0c8a52-7d4f-4f6e-9a57-3b1c2d0e9f11")


class SuscripcionesHTTP:
    """Consulta la decisión de HU-13 en ms-suscripcion: GET /v1/suscripciones/{solicitud_id}.
    ms-suscripcion exige autenticación: se genera un token de servicio nuevo en cada
    llamada (dura 5 minutos, no se puede reusar de un arranque a otro del proceso)."""

    def __init__(self, http: httpx.AsyncClient, secreto: str) -> None:
        self._http = http
        self._secreto = secreto

    async def aceptada(self, solicitud_id: UUID) -> bool:
        try:
            respuesta = await self._http.get(
                f"/v1/suscripciones/{solicitud_id}",
                headers={"Authorization": f"Bearer {token_de_servicio(self._secreto, 'ms-pagos')}"},
            )
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
    referencia externa se deriva de la clave, así un mismo cobro siempre tiene la misma referencia.
    En el ambiente de integración (HU-88) se le puede forzar demora y caída; caída se reporta como
    DependenciaNoDisponible, igual que lo haría un adaptador HTTP real."""

    proveedor = "stub"

    def __init__(self, latencia_ms: int = 0, fallar: bool = False) -> None:
        self._latencia_ms = latencia_ms
        self._fallar = fallar

    async def cobrar(self, token_medio_pago: str, monto: Decimal, idempotency_key: str) -> ResultadoPasarela:
        await asyncio.sleep(self._latencia_ms / 1000)
        if self._fallar:
            raise DependenciaNoDisponible("la pasarela de pagos")
        estado = EstadoPago.RECHAZADO if token_medio_pago == TOKEN_RECHAZO else EstadoPago.APROBADO
        return ResultadoPasarela(
            estado=estado,
            proveedor=self.proveedor,
            referencia_externa=f"stub-{uuid5(_ESPACIO_STUB, idempotency_key)}",
        )
