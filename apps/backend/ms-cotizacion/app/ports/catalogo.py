from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


class DefinicionDatoRiesgo(Protocol):
    def valido(self, valor: Any) -> bool: ...

    def describir_rango(self) -> str: ...


@dataclass(frozen=True)
class RangoNumerico:
    minimo: float
    maximo: float

    def valido(self, valor: Any) -> bool:
        try:
            return self.minimo <= float(valor) <= self.maximo
        except (TypeError, ValueError):
            return False

    def describir_rango(self) -> str:
        return f"entre {self.minimo} y {self.maximo}"


@dataclass(frozen=True)
class ValoresPermitidos:
    valores: tuple[str, ...]

    def valido(self, valor: Any) -> bool:
        return valor in self.valores

    def describir_rango(self) -> str:
        return f"uno de: {', '.join(self.valores)}"


@dataclass(frozen=True)
class DefinicionProducto:
    producto: str
    coberturas: list[str]
    datos_riesgo: dict[str, DefinicionDatoRiesgo]


class CatalogoProductos(Protocol):
    def obtener(self, producto: str) -> DefinicionProducto | None: ...
