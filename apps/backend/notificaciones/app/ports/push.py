from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol
from uuid import UUID

from app.domain.modelos import DispositivoPush, Notificacion


class EstadoEnvio(StrEnum):
    ENVIADO = "enviado"
    TOKEN_INVALIDO = "token_invalido"
    NO_DISPONIBLE = "no_disponible"


@dataclass(frozen=True)
class ResultadoEnvio:
    dispositivo_id: UUID
    estado: str
    proveedor_id: str | None = None


class EnviadorPush(Protocol):
    async def enviar(self, dispositivo: DispositivoPush, notificacion: Notificacion) -> str: ...

    async def enviar_a_usuario(
        self, dispositivos: list[DispositivoPush], notificacion: Notificacion
    ) -> list[ResultadoEnvio]: ...
