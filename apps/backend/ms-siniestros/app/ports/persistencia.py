from __future__ import annotations

from collections.abc import Callable
from typing import Protocol
from uuid import UUID

from app.domain.modelos import (
    EvaluacionUmbral,
    EventoDominio,
    EventoParametrico,
    PagoParametrico,
    Siniestro,
)


class ClaveIdempotenciaDuplicada(Exception):
    """Carrera de idempotencia: otra transacción confirmó primero el mismo evento_id."""


class RepositorioSiniestros(Protocol):
    async def obtener(self, siniestro_id: UUID) -> Siniestro | None: ...

    async def obtener_por_evento(self, evento_id: str) -> Siniestro | None: ...

    async def listar(self, limite: int) -> list[Siniestro]: ...

    async def listar_abiertos_por_poliza(self, poliza_id: UUID) -> list[Siniestro]: ...

    async def agregar(self, siniestro: Siniestro) -> None: ...

    async def actualizar(self, siniestro: Siniestro) -> None: ...


class RepositorioEventosParametricos(Protocol):
    async def obtener_por_clave(self, evento_id: str) -> EventoParametrico | None: ...

    async def agregar(self, evento: EventoParametrico) -> None: ...


class RepositorioEvaluaciones(Protocol):
    async def obtener_por_evento(self, evento_id: str) -> EvaluacionUmbral | None: ...

    async def agregar(self, evaluacion: EvaluacionUmbral) -> None: ...


class RepositorioPagos(Protocol):
    async def obtener_por_evento(self, evento_id: str) -> PagoParametrico | None: ...

    async def agregar(self, pago: PagoParametrico) -> None: ...


class Outbox(Protocol):
    async def agregar(self, evento: EventoDominio) -> None: ...


class UnidadDeTrabajo(Protocol):
    siniestros: RepositorioSiniestros
    eventos_parametricos: RepositorioEventosParametricos
    evaluaciones: RepositorioEvaluaciones
    pagos: RepositorioPagos
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None: ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
