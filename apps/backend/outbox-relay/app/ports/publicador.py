from __future__ import annotations

from typing import Protocol

from app.domain.modelos import EventoOutbox


class PublicadorEventos(Protocol):
    async def publicar(self, evento: EventoOutbox) -> None: ...

    async def cerrar(self) -> None: ...
