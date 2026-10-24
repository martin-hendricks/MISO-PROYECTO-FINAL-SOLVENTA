from __future__ import annotations

from typing import Protocol
from uuid import UUID


class VerificadorSuscripcion(Protocol):
    """¿La suscripción de la solicitud fue aceptada? (HU-13, ms-suscripcion)."""

    async def aceptada(self, solicitud_id: UUID) -> bool: ...


class VerificadorCobro(Protocol):
    """¿El cobro de la prima de la oferta tuvo éxito? (HU-15, ms-pagos)."""

    async def exitoso(self, oferta_id: UUID, referencia_cobro: str) -> bool: ...
