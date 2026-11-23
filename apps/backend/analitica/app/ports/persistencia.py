from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Protocol

from app.domain.modelos import ConteoEventos


class EventoYaProcesado(Exception):
    """El `evento_id` ya incrementó un contador antes -- no se repite (idempotencia)."""


class RepositorioMetricas(Protocol):
    async def incrementar(self, evento_id_str: str, tipo: str, fecha: date) -> bool:
        """Suma 1 al contador de (tipo, fecha). Devuelve False si `evento_id_str`
        ya se procesó antes (idempotencia), True si incrementó de verdad."""
        ...

    async def listar(self, desde: date, hasta: date) -> list[ConteoEventos]: ...


class UnidadDeTrabajo(Protocol):
    metricas: RepositorioMetricas

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None: ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
