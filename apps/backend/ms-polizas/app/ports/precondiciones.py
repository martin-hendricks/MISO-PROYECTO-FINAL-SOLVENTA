from __future__ import annotations

from typing import Protocol
from uuid import UUID


class VerificadorSuscripcion(Protocol):
    """¿La suscripción de la solicitud fue aceptada? (HU-13, ms-suscripcion)."""

    async def aceptada(self, solicitud_id: UUID) -> bool: ...


class VerificadorCobro(Protocol):
    """¿El pago confirmado es un cobro aprobado de la prima de esta oferta? (HU-15, ms-pagos).
    El token es el `pago_id` del cobro: el TokenPagoConfirmado de ComandoEmisionDTO."""

    async def exitoso(self, oferta_id: UUID, token_pago_confirmado: UUID) -> bool: ...
