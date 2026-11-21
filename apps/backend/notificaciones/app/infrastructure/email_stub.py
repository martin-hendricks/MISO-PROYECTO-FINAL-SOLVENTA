from __future__ import annotations

from uuid import uuid4

from app.domain.errores import ServicioExternoNoDisponible


class EmailStub:
    """Adaptador determinista de correo para desarrollo y pruebas: no envía nada."""

    def __init__(self, fallar: bool = False) -> None:
        self._fallar = fallar

    async def enviar(self, destinatario: str, asunto: str, cuerpo: str) -> str:
        if self._fallar:
            raise ServicioExternoNoDisponible("Proveedor de correo no disponible (stub)")
        return f"stub-email-{uuid4()}"
