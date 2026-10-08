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
    def obtener(self, producto: str) -> DefinicionProducto | None: ...
