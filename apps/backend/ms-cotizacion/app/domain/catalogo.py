"""Definición de producto del catálogo (HU-1) y validación de los datos del riesgo.

Agregar un producto es dato, no código (EC-MOD-01): cada producto declara sus campos
del riesgo y el rango válido de cada uno; la validación es la misma para todos.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Any

from .errores import DatoRiesgoInvalido


class TipoDato(StrEnum):
    ENTERO = "entero"
    TEXTO = "texto"
    BOOLEANO = "booleano"


@dataclass(frozen=True)
class CampoRiesgo:
    nombre: str
    tipo: TipoDato
    minimo: int | None = None
    maximo: int | None = None

    def rango_valido(self) -> dict:
        rango: dict = {"tipo": self.tipo.value}
        if self.minimo is not None:
            rango["min"] = self.minimo
        if self.maximo is not None:
            rango["max"] = self.maximo
        return rango

    def validar(self, valor: Any) -> Any:
        if self.tipo is TipoDato.BOOLEANO:
            if not isinstance(valor, bool):
                raise self._tipo_invalido()
            return valor

        if self.tipo is TipoDato.ENTERO:
            # bool es subclase de int en Python: se rechaza explícitamente.
            if isinstance(valor, bool) or not isinstance(valor, int):
                raise self._tipo_invalido()
            medida = valor
        else:
            if not isinstance(valor, str):
                raise self._tipo_invalido()
            valor = valor.strip()
            medida = len(valor)

        if (self.minimo is not None and medida < self.minimo) or (
            self.maximo is not None and medida > self.maximo
        ):
            unidad = " caracteres" if self.tipo is TipoDato.TEXTO else ""
            raise DatoRiesgoInvalido(
                "dato_riesgo_fuera_de_rango",
                self.nombre,
                f"'{self.nombre}' fuera de rango: debe estar entre {self.minimo} y {self.maximo}{unidad}",
                self.rango_valido(),
            )
        return valor

    def _tipo_invalido(self) -> DatoRiesgoInvalido:
        return DatoRiesgoInvalido(
            "dato_riesgo_tipo_invalido",
            self.nombre,
            f"'{self.nombre}' debe ser de tipo {self.tipo.value}",
            self.rango_valido(),
        )


@dataclass(frozen=True)
class Cobertura:
    codigo: str
    nombre: str
    limite: Decimal


@dataclass(frozen=True)
class Producto:
    codigo: str
    nombre: str
    moneda: str
    coberturas: tuple[Cobertura, ...]
    campos_riesgo: tuple[CampoRiesgo, ...] = field(default_factory=tuple)

    def validar_datos_riesgo(self, datos: dict[str, Any]) -> dict[str, Any]:
        """Devuelve los datos normalizados o lanza DatoRiesgoInvalido con el primer campo que falla."""
        esperados = {c.nombre for c in self.campos_riesgo}
        sobrantes = sorted(set(datos) - esperados)
        if sobrantes:
            raise DatoRiesgoInvalido(
                "dato_riesgo_no_reconocido",
                sobrantes[0],
                f"'{sobrantes[0]}' no es un dato del riesgo de {self.codigo}",
            )

        normalizados: dict[str, Any] = {}
        for campo in self.campos_riesgo:
            if campo.nombre not in datos or datos[campo.nombre] is None:
                raise DatoRiesgoInvalido(
                    "dato_riesgo_faltante",
                    campo.nombre,
                    f"'{campo.nombre}' es obligatorio",
                    campo.rango_valido(),
                )
            normalizados[campo.nombre] = campo.validar(datos[campo.nombre])
        return normalizados
