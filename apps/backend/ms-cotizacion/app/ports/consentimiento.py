from __future__ import annotations

from typing import Protocol
from uuid import UUID


class ConsentimientoPerfil(Protocol):
    def requiere(self, producto: str) -> bool: ...

    async def vigente(self, usuario_id: UUID) -> bool: ...
