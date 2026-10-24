from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.domain.modelos import EventoDominio, Pago


class ClaveIdempotenciaDuplicada(Exception):
    """Otra transacción registró el cobro con la misma clave antes del commit."""


class RepositorioPagos(Protocol):
    async def obtener(self, pago_id: UUID) -> Pago | None: ...

    async def obtener_por_clave(self, idempotency_key: str) -> Pago | None: ...

    async def agregar(self, pago: Pago, token_medio_pago: str) -> None: ...


class Outbox(Protocol):
    async def agregar(self, evento: EventoDominio) -> None: ...


class UnidadDeTrabajo(Protocol):
    pagos: RepositorioPagos
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None:
        ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
