from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.domain.modelos import Consentimiento, EventoDominio, Oferta


class ClaveIdempotenciaDuplicada(Exception):
    pass


class RepositorioConsentimientos(Protocol):
    async def obtener_vigente(self, cliente_id: str) -> Consentimiento | None:
        """Debe devolver el consentimiento SOLO si está vigente (no revocado). Nunca
        cachea: cada llamada refleja el último estado persistido (HU-53)."""
        ...

    async def obtener_por_id(self, consentimiento_id: UUID) -> Consentimiento | None: ...

    async def agregar(self, consentimiento: Consentimiento) -> None: ...

    async def actualizar(self, consentimiento: Consentimiento) -> None: ...


class RepositorioOfertas(Protocol):
    async def obtener(self, oferta_id: UUID) -> Oferta | None: ...

    async def obtener_por_clave(self, idempotency_key: str) -> Oferta | None: ...

    async def agregar(self, idempotency_key: str, oferta: Oferta) -> None: ...


class Outbox(Protocol):
    async def agregar(self, evento: EventoDominio) -> None: ...


class UnidadDeTrabajo(Protocol):
    consentimientos: RepositorioConsentimientos
    ofertas: RepositorioOfertas
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None: ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
