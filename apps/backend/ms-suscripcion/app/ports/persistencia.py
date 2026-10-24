from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.domain.modelos import EventoDominio, ReglaSuscripcion, Suscripcion


class SolicitudYaDecidida(Exception):
    pass


class RepositorioSuscripciones(Protocol):
    async def obtener_por_solicitud(self, solicitud_id: UUID) -> Suscripcion | None: ...

    async def agregar(self, suscripcion: Suscripcion) -> None: ...


class RepositorioReglas(Protocol):
    async def vigente(self) -> ReglaSuscripcion | None: ...


class Outbox(Protocol):
    async def agregar(self, evento: EventoDominio) -> None: ...


class UnidadDeTrabajo(Protocol):
    suscripciones: RepositorioSuscripciones
    reglas: RepositorioReglas
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None:
        ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
