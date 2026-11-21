from __future__ import annotations

from typing import Protocol
from uuid import UUID


class EnviadorEmail(Protocol):
    async def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> str:
        """Envía un correo de texto plano y devuelve el id del proveedor."""
        ...


class ResolutorDestinatario(Protocol):
    async def correo_de(self, usuario_id: UUID) -> str | None:
        """Correo del usuario, o `None` si no existe o no tiene uno."""
        ...
