from __future__ import annotations

from collections.abc import Callable
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

    async def obtener_por_numero(self, numero: str) -> Poliza | None: ...

    async def actualizar(self, poliza: Poliza) -> None: ...


class RepositorioFirmas(Protocol):
    async def agregar(self, constancia: ConstanciaFirma) -> None: ...

    async def ultima_por_oferta(self, oferta_id: UUID) -> ConstanciaFirma | None: ...


class Outbox(Protocol):
    async def agregar(self, evento: EventoDominio) -> None: ...


class UnidadDeTrabajo(Protocol):
    polizas: RepositorioPolizas
    firmas: RepositorioFirmas
    outbox: Outbox

    async def __aenter__(self) -> UnidadDeTrabajo: ...

    async def __aexit__(self, *exc: object) -> None: ...

    async def confirmar(self) -> None:
        ...


FabricaUnidadDeTrabajo = Callable[[], UnidadDeTrabajo]
