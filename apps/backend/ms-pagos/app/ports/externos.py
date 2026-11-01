from __future__ import annotations

from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.domain.modelos import ResultadoPasarela


class VerificadorSuscripcion(Protocol):
    """¿La suscripción de la solicitud fue aceptada? (HU-13, ms-suscripcion)."""

    async def aceptada(self, solicitud_id: UUID) -> bool: ...


class PasarelaPagos(Protocol):
    async def cobrar(self, token_medio_pago: str, monto: Decimal, idempotency_key: str) -> ResultadoPasarela: ...
