from __future__ import annotations

from collections.abc import Callable
from datetime import date
from typing import Protocol
from uuid import UUID

from app.domain.modelos import ConstanciaFirma, EventoDominio, Poliza


class PolizaYaEmitida(Exception):
    """Otra transacción emitió la póliza de la misma oferta antes del commit."""


class RepositorioPolizas(Protocol):
    async def obtener(self, poliza_id: UUID) -> Poliza | None: ...

    async def obtener_por_oferta(self, oferta_id: UUID) -> Poliza | None: ...

    async def siguiente_secuencia(self) -> int: ...

    async def agregar(self, poliza: Poliza) -> None: ...

    async def listar_por_usuario(self, usuario_id: UUID, limite: int) -> list[Poliza]: ...

    async def ofertas_con_poliza(self, oferta_ids: list[UUID]) -> set[UUID]: ...

    async def obtener_por_numero(self, numero: str) -> Poliza | None: ...

    async def actualizar(self, poliza: Poliza) -> None: ...

    async def listar_por_vencer(
        self, hoy: date, hasta: date, usuario_id: UUID | None = None
    ) -> list[Poliza]: ...

    async def listar_emitidas_entre(self, desde: date, hasta: date) -> list[Poliza]: ...

    async def listar_canceladas_entre(self, desde: date, hasta: date) -> list[Poliza]: ...


class RepositorioFirmas(Protocol):
    async def agregar(self, constancia: ConstanciaFirma) -> None: ...

    async def ultima_por_oferta(self, oferta_id: UUID) -> ConstanciaFirma | None: ...


class Outbox(Protocol):
    async def agregar(self, evento: EventoDominio) -> None: ...

    async def existe_para_agregado(self, tipo: str, agregado_id: UUID) -> bool:
        """HU-67: idempotencia del job de avisos de vencimiento -- evita
        generar un "PolizaPorVencer" nuevo en cada corrida mientras la misma
        póliza siga dentro de la ventana (correría a diario sobre la misma
        póliza por hasta `dias` días seguidos sin esto)."""
        ...


class UnidadDeTrabajo(Protocol):
    polizas: RepositorioPolizas
    firmas: RepositorioFirmas
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None:
        ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
