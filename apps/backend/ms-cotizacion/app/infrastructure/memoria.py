"""Ofertas vigentes en memoria del proceso.

PROVISIONAL: no se comparte entre réplicas (ms-cotizacion corre con 4+ en EKS), así que HU-7
no puede reconsultar de forma fiable fuera de una sola instancia. Pendiente decidir el almacén
(ms_cotizacion en PostgreSQL o Redis con TTL = vigencia). Sin histórico: lo vencido se purga.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.domain.modelos import Cotizacion


class RepositorioCotizacionesEnMemoria:
    def __init__(self) -> None:
        self._vigentes: dict[UUID, Cotizacion] = {}

    async def guardar(self, cotizacion: Cotizacion) -> None:
        self._purgar(cotizacion.creada_en)
        self._vigentes[cotizacion.id] = cotizacion

    async def obtener_vigente(self, cotizacion_id: UUID, ahora: datetime) -> Cotizacion | None:
        self._purgar(ahora)
        return self._vigentes.get(cotizacion_id)

    def _purgar(self, ahora: datetime) -> None:
        vencidas = [i for i, c in self._vigentes.items() if not c.vigente_en(ahora)]
        for cotizacion_id in vencidas:
            del self._vigentes[cotizacion_id]


class RelojSistema:
    def ahora(self) -> datetime:
        return datetime.now(UTC)
