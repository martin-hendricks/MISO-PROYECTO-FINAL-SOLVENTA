from __future__ import annotations

from typing import Protocol
from uuid import UUID


class EnviadorEmail(Protocol):
    async def enviar(
        self, destinatario: str, asunto: str, cuerpo: str, cuerpo_html: str | None = None
    ) -> str:
        """Envía el correo y devuelve el id del proveedor. `cuerpo` es el texto plano;
        `cuerpo_html`, si se da, viaja como alternativa multipart para los clientes
        que renderizan HTML."""
        ...


class ResolutorDestinatario(Protocol):
    async def correo_de(self, usuario_id: UUID) -> str | None:
        """Correo del usuario, o `None` si no existe o no tiene uno."""
        ...
