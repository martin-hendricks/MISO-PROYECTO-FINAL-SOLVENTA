from __future__ import annotations

from typing import Protocol

from app.domain.catalogo import (
    Cobertura,
    DefinicionDatoRiesgo,
    DefinicionProducto,
    RangoNumerico,
    UnidadLimite,
    ValoresPermitidos,
)

__all__ = [
    "CatalogoProductos",
    "Cobertura",
    "DefinicionDatoRiesgo",
    "DefinicionProducto",
    "RangoNumerico",
    "UnidadLimite",
    "ValoresPermitidos",
]


class CatalogoProductos(Protocol):
    """Solo lectura: no hay operación de alta ni de edición de productos (HU-1)."""

    def obtener(self, producto: str) -> DefinicionProducto | None: ...
