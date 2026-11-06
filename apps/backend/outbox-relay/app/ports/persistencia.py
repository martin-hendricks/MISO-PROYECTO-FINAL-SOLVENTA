from __future__ import annotations

from datetime import datetime
from typing import Protocol

from app.ports.publicador import PublicadorEventos


class RepositorioOutbox(Protocol):
    async def publicar_pendientes(
        self, publicador: PublicadorEventos, lote: int, ahora: datetime
    ) -> int: ...
