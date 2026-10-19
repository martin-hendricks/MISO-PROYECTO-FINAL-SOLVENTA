from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.domain.modelos import EventoDominio, SolicitudCotizacion
from app.ports.oferta import RepositorioOfertas
from app.ports.rating import RepositorioReglasRating


class ClaveIdempotenciaDuplicada(Exception):
    pass


class RepositorioSolicitudes(Protocol):
    async def obtener(self, solicitud_id: UUID) -> SolicitudCotizacion | None: ...

    async def obtener_por_clave(self, idempotency_key: str) -> SolicitudCotizacion | None: ...

    async def agregar(self, solicitud: SolicitudCotizacion) -> None: ...

    async def actualizar(self, solicitud: SolicitudCotizacion) -> None: ...


class Outbox(Protocol):
    async def agregar(self, evento: EventoDominio) -> None: ...


class UnidadDeTrabajo(Protocol):
    solicitudes: RepositorioSolicitudes
    reglas_rating: RepositorioReglasRating
    ofertas: RepositorioOfertas
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None: ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
