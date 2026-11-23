from __future__ import annotations

import asyncio
from collections.abc import Iterable

from app.domain.errores import DependenciaNoDisponible


class VerificadorKYCStub:
    """Doble del proveedor KYC (HU-88), sin integrarse con ninguno real. Por defecto aprueba
    todo documento, así que no cambia el alta respecto a no tener KYC. En el ambiente de
    integración se configura qué documentos rechaza y se le puede forzar demora y caída."""

    def __init__(self, latencia_ms: int = 0, fallar: bool = False, documentos_rechazados: Iterable[str] = ()) -> None:
        self._latencia_ms = latencia_ms
        self._fallar = fallar
        self._documentos_rechazados = frozenset(documentos_rechazados)

    async def verificar(self, tipo_documento: str, numero_documento: str) -> bool:
        await asyncio.sleep(self._latencia_ms / 1000)
        if self._fallar:
            raise DependenciaNoDisponible("el verificador KYC")
        return numero_documento not in self._documentos_rechazados
