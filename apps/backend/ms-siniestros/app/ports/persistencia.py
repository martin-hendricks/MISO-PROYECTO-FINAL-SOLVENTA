from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.aviso import Adjunto, Decision, IntentoPago, PagoSiniestro, ParametroRamo
from app.domain.modelos import (
    EstadoSiniestro,
    EvaluacionUmbral,
    EventoDominio,
    EventoParametrico,
    PagoParametrico,
    ResultadoDecision,
    Siniestro,
    TipoSiniestro,
)


class ClaveIdempotenciaDuplicada(Exception):
    """Carrera de idempotencia: otra transacción confirmó primero el mismo evento_id."""


@dataclass(frozen=True)
class FiltroSiniestros:
    """Filtros de la lista del cliente (usuario_id) y de la cola del operador
    (requiere_revision / resultado). Todos opcionales: sin filtros es la lista completa."""

    usuario_id: UUID | None = None
    tipo: TipoSiniestro | None = None
    estado: EstadoSiniestro | None = None
    resultado: ResultadoDecision | None = None
    requiere_revision: bool | None = None
    limite: int = 20


class RepositorioSiniestros(Protocol):
    async def obtener(self, siniestro_id: UUID) -> Siniestro | None: ...

    async def obtener_por_evento(self, evento_id: str) -> Siniestro | None: ...

    async def obtener_por_clave_idempotencia(self, clave: str) -> Siniestro | None: ...

    async def listar(self, limite: int, usuario_id: UUID | None = None) -> list[Siniestro]: ...

    async def filtrar(self, filtro: FiltroSiniestros) -> list[Siniestro]: ...

    async def listar_abiertos_por_poliza(self, poliza_id: UUID) -> list[Siniestro]: ...

    async def contar_avisos_de_poliza_desde(self, poliza_id: UUID, desde: datetime, excluir: UUID) -> int: ...

    async def tomar_pendientes_de_evaluacion(self, limite: int) -> list[Siniestro]:
        """Avisos asistidos en RECIBIDO, bloqueados para esta transacción (SKIP LOCKED):
        dos réplicas del worker nunca evalúan el mismo aviso."""
        ...

    async def agregar(self, siniestro: Siniestro) -> None: ...

    async def actualizar(self, siniestro: Siniestro) -> None: ...


class RepositorioAdjuntos(Protocol):
    async def listar_de(self, siniestro_id: UUID) -> list[Adjunto]: ...

    async def agregar(self, adjunto: Adjunto) -> None: ...


class RepositorioDecisiones(Protocol):
    async def listar_de(self, siniestro_id: UUID) -> list[Decision]: ...

    async def agregar(self, decision: Decision) -> None: ...


class RepositorioPagosSiniestro(Protocol):
    async def obtener_de(self, siniestro_id: UUID) -> PagoSiniestro | None: ...

    async def agregar(self, pago: PagoSiniestro) -> None: ...

    async def registrar_intento(self, intento: IntentoPago) -> None: ...

    async def listar_intentos(self, siniestro_id: UUID) -> list[IntentoPago]: ...


class RepositorioParametros(Protocol):
    async def obtener(self, ramo: str) -> ParametroRamo | None: ...

    async def listar(self) -> list[ParametroRamo]: ...


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
    adjuntos: RepositorioAdjuntos
    decisiones: RepositorioDecisiones
    pagos_siniestro: RepositorioPagosSiniestro
    parametros: RepositorioParametros
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None: ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
