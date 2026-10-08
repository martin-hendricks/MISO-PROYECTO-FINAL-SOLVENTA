from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping, Protocol


class UnidadLimite(StrEnum):
    SMLDV = "SMLDV"
    MONEDA = "MONEDA"


@dataclass(frozen=True)
class Cobertura:
    codigo: str
    nombre: str
    limite: Decimal
    unidad_limite: UnidadLimite


class DefinicionDatoRiesgo(Protocol):
    def valido(self, valor: Any) -> bool: ...

    def describir_rango(self) -> str: ...


@dataclass(frozen=True)
class RangoNumerico:
    minimo: Decimal
    maximo: Decimal

    def valido(self, valor: Any) -> bool:
        if isinstance(valor, bool):
            return False
        try:
            return self.minimo <= Decimal(str(valor)) <= self.maximo
        except (InvalidOperation, ValueError):
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
    nombre: str
    moneda: str
    coberturas: tuple[Cobertura, ...]
    datos_riesgo: Mapping[str, DefinicionDatoRiesgo]

    def __post_init__(self) -> None:
        object.__setattr__(self, "coberturas", tuple(self.coberturas))
        object.__setattr__(self, "datos_riesgo", MappingProxyType(dict(self.datos_riesgo)))

    @property
    def codigos_coberturas(self) -> list[str]:
        return [c.codigo for c in self.coberturas]
