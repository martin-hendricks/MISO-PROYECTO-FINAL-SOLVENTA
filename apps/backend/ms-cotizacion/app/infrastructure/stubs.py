"""Stubs de colaboradores de otras HU. Se sustituyen en dependencies.py, sin tocar el caso de uso."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from app.domain.catalogo import Producto


class PrimaFijaStub:
    """PENDIENTE HU-4 (SOLV-97): prima con reglas. Devuelve una prima fija por producto."""

    def __init__(self, prima: Decimal = Decimal("89000")) -> None:
        self._prima = prima

    async def calcular(self, producto: Producto, datos_riesgo: dict[str, Any]) -> Decimal:
        return self._prima


class FactorRiesgoNeutroStub:
    """PENDIENTE HU-5 (SOLV-98): factor de riesgo (Open Finance en stub en el MVP). Factor neutro."""

    async def obtener(self, producto: Producto, datos_riesgo: dict[str, Any]) -> Decimal:
        return Decimal("1")
