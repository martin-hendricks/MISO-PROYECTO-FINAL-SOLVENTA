from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from app.domain.modelos import Ejemplo, EventoDominio


class ClaveIdempotenciaDuplicada(Exception):
    pass


class RepositorioEjemplos(Protocol):
    async def obtener(self, ejemplo_id: UUID) -> Ejemplo | None: ...

    async def obtener_por_clave(self, idempotency_key: str) -> Ejemplo | None: ...

    async def listar(self, limite: int) -> list[Ejemplo]: ...

    async def indicadores(self) -> tuple[int, Decimal]: ...

    async def agregar(self, ejemplo: Ejemplo) -> None: ...

    async def actualizar(self, ejemplo: Ejemplo) -> None: ...


class Outbox(Protocol):
    async def agregar(self, evento: EventoDominio) -> None: ...


class UnidadDeTrabajo(Protocol):
    ejemplos: RepositorioEjemplos
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None:
        ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
