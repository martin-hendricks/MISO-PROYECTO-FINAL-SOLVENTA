from __future__ import annotations

from typing import Protocol

from app.domain.rating import ReglaRating


class RepositorioReglasRating(Protocol):
    async def obtener_vigente(self, producto: str) -> ReglaRating | None: ...
