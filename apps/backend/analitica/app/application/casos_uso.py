from __future__ import annotations

from datetime import date

from app.domain.modelos import ConteoEventos
from app.ports.persistencia import FabricaUnidadDeTrabajo


async def listar_metricas(uow: FabricaUnidadDeTrabajo, desde: date, hasta: date) -> list[ConteoEventos]:
    async with uow() as tx:
        return await tx.metricas.listar(desde, hasta)
