from __future__ import annotations

from typing import Protocol
from uuid import UUID

from app.domain.oferta import Oferta


class RepositorioOfertas(Protocol):
    async def obtener(self, oferta_id: UUID) -> Oferta | None: ...

    async def obtener_por_solicitud(self, solicitud_id: UUID) -> Oferta | None: ...

    async def agregar(self, oferta: Oferta) -> None: ...
