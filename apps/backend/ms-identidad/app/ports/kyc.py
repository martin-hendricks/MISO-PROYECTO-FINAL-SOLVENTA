from __future__ import annotations

from typing import Protocol


class VerificadorKYC(Protocol):
    """Puerto SUSTITUIBLE (HU-88) hacia el proveedor de verificación de identidad (KYC). El
    caso de uso de alta solo conoce este Protocol: no distingue el doble del proveedor real.
    Un proveedor caído se reporta como DependenciaNoDisponible, nunca como rechazo."""

    async def verificar(self, tipo_documento: str, numero_documento: str) -> bool:
        """True si el documento pasa la verificación; False si el proveedor lo rechaza."""
        ...
