from __future__ import annotations

from typing import Protocol

from app.domain.modelos import DispositivoPush, Notificacion


class EnviadorPush(Protocol):
    async def enviar(self, dispositivo: DispositivoPush, notificacion: Notificacion) -> str: ...

    async def enviar_a_usuario(
        self, dispositivos: list[DispositivoPush], notificacion: Notificacion
    ) -> list[str]: ...
