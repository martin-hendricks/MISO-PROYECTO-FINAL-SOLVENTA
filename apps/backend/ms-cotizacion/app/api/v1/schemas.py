from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.domain.catalogo import (
    Booleano,
    Cobertura,
    DefinicionDatoRiesgo,
    DefinicionProducto,
    RangoNumerico,
    TextoLibre,
    ValoresPermitidos,
)


class CoberturaSalida(BaseModel):
    codigo: str
    nombre: str
    limite: Decimal
    unidad_limite: str

    @classmethod
    def desde(cls, cobertura: Cobertura) -> CoberturaSalida:
        return cls(
            codigo=cobertura.codigo,
            nombre=cobertura.nombre,
            limite=cobertura.limite,
            unidad_limite=cobertura.unidad_limite.value,
        )


class DatoRiesgoSalida(BaseModel):
    nombre: str
    tipo: Literal["rango", "valores", "texto", "booleano"]
    minimo: Decimal | None = None
    maximo: Decimal | None = None
    valores: list[str] | None = None
    obligatorio: bool = True

    @classmethod
    def desde(cls, nombre: str, dato: DefinicionDatoRiesgo) -> DatoRiesgoSalida:
        if isinstance(dato, RangoNumerico):
            return cls(nombre=nombre, tipo="rango", minimo=dato.minimo, maximo=dato.maximo)
        if isinstance(dato, ValoresPermitidos):
            return cls(nombre=nombre, tipo="valores", valores=list(dato.valores))
        if isinstance(dato, TextoLibre):
            return cls(nombre=nombre, tipo="texto")
        if isinstance(dato, Booleano):
            return cls(nombre=nombre, tipo="booleano")
        raise TypeError(f"Dato de riesgo sin representación pública: {type(dato).__name__}")


class ProductoSalida(BaseModel):
    producto: str
    nombre: str
    descripcion: str
    moneda: str
    disponible: bool
    coberturas: list[CoberturaSalida]
    datos_riesgo: list[DatoRiesgoSalida]

    @classmethod
    def desde(cls, definicion: DefinicionProducto) -> ProductoSalida:
        return cls(
            producto=definicion.producto,
            nombre=definicion.nombre,
            descripcion=definicion.descripcion,
            moneda=definicion.moneda,
            disponible=definicion.disponible(),
            coberturas=[CoberturaSalida.desde(c) for c in definicion.coberturas],
            datos_riesgo=[DatoRiesgoSalida.desde(n, d) for n, d in definicion.datos_riesgo.items()],
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
