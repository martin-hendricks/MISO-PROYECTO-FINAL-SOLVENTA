"""Puertos que necesita el caso de uso de cotización (DIP).

Cada colaborador de otra HU entra por aquí, así la HU-3 avanza con stubs y se
sustituye la implementación sin tocar el caso de uso:
  Catalogo           -> HU-1 (catálogo mínimo)
  CalculadoraPrima   -> HU-4 (prima con reglas)
  FuenteFactorRiesgo -> HU-5 (factor de riesgo, stub de Open Finance en el MVP)
  RepositorioCotizaciones -> almacén de ofertas vigentes que reconsulta HU-7
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Protocol
from uuid import UUID

from app.domain.catalogo import Producto
from app.domain.modelos import Cotizacion


class Catalogo(Protocol):
    async def obtener(self, codigo_producto: str) -> Producto | None: ...


class CalculadoraPrima(Protocol):
    async def calcular(self, producto: Producto, datos_riesgo: dict[str, Any]) -> Decimal: ...


class FuenteFactorRiesgo(Protocol):
    async def obtener(self, producto: Producto, datos_riesgo: dict[str, Any]) -> Decimal: ...


class RepositorioCotizaciones(Protocol):
    async def guardar(self, cotizacion: Cotizacion) -> None: ...

    async def obtener_vigente(self, cotizacion_id: UUID, ahora: datetime) -> Cotizacion | None: ...


class Reloj(Protocol):
    def ahora(self) -> datetime: ...
