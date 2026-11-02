from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.domain.modelos import EstadoSolicitud, EventoDominio, SolicitudCotizacion
from app.domain.oferta import Oferta
from app.ports.oferta import RepositorioOfertas
from app.ports.rating import RepositorioReglasRating


class ClaveIdempotenciaDuplicada(Exception):
    pass


class AceptacionConcurrente(Exception):
    """Otra aceptación de la misma cotización confirmó primero."""


class RepositorioSolicitudes(Protocol):
    async def obtener(self, solicitud_id: UUID) -> SolicitudCotizacion | None: ...

    async def obtener_por_clave(self, idempotency_key: str) -> SolicitudCotizacion | None: ...

    async def agregar(self, solicitud: SolicitudCotizacion) -> None: ...

    async def actualizar(self, solicitud: SolicitudCotizacion) -> None: ...

    async def registrar_aceptacion(self, solicitud: SolicitudCotizacion) -> None:
        """Escritura condicional: solo pasa de cotizada a aceptada. Lanza
        AceptacionConcurrente si otra aceptación ganó la carrera."""
        ...

    async def listar_por_asesor(
        self,
        asesor_id: UUID,
        estados: frozenset[EstadoSolicitud],
        vigentes_desde: datetime | None,
        desplazamiento: int,
        limite: int,
    ) -> list[tuple[SolicitudCotizacion, Oferta]]:
        """HU-163: cotizaciones del asesor con su oferta, por creada_en descendente.
        Con vigentes_desde, excluye en la consulta las ofertas con vence_en <= ese instante."""
        ...


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
