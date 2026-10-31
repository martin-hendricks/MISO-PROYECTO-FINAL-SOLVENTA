from __future__ import annotations

import asyncio

from app.domain.errores import DependenciaNoDisponible

DOCUMENTO_RECHAZO = "0000000000"


class VerificadorKYCStub:
    """Doble del proveedor KYC (HU-88), sin integrarse con ninguno real. Es determinista: el
    documento `0000000000` se rechaza y cualquier otro se aprueba. En el ambiente de integración
    se le puede forzar demora y caída por configuración."""

    def __init__(self, latencia_ms: int = 0, fallar: bool = False) -> None:
        self._latencia_ms = latencia_ms
        self._fallar = fallar

    async def verificar(self, tipo_documento: str, numero_documento: str) -> bool:
        await asyncio.sleep(self._latencia_ms / 1000)
        if self._fallar:
            raise DependenciaNoDisponible("el verificador KYC")
        return numero_documento != DOCUMENTO_RECHAZO
