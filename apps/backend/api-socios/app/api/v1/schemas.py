from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class ModeloVista(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


# Contrato público del catálogo para socios (HU-2). Es propio de Solventa: no replica el
# modelo del núcleo ni sus tablas. Un campo nuevo siempre entra como opcional (EC-MOD-01);
# quitar o renombrar uno es /v2.


class LimiteVista(ModeloVista):
    valor: Decimal
    unidad: str


class CoberturaVista(ModeloVista):
    codigo: str
    nombre: str
    limite: LimiteVista

    @classmethod
    def desde_nucleo(cls, dato: dict) -> CoberturaVista:
        return cls(
            codigo=dato["codigo"],
            nombre=dato["nombre"],
            limite=LimiteVista(valor=Decimal(str(dato["limite"])), unidad=dato["unidad_limite"]),
        )


class DatoRiesgoVista(ModeloVista):
    nombre: str
    tipo: Literal["rango", "valores"]
    minimo: Decimal | None = None
    maximo: Decimal | None = None
    valores: list[str] | None = None

    @classmethod
    def desde_nucleo(cls, dato: dict) -> DatoRiesgoVista:
        if dato["tipo"] == "rango":
            return cls(
                nombre=dato["nombre"],
                tipo="rango",
                minimo=Decimal(str(dato["minimo"])),
                maximo=Decimal(str(dato["maximo"])),
            )
        return cls(nombre=dato["nombre"], tipo="valores", valores=list(dato["valores"]))


class ProductoVista(ModeloVista):
    codigo: str
    nombre: str
    moneda: str
    coberturas: list[CoberturaVista]
    datos_riesgo: list[DatoRiesgoVista]

    @classmethod
    def desde_nucleo(cls, dato: dict) -> ProductoVista:
        return cls(
            codigo=dato["producto"],
            nombre=dato["nombre"],
            moneda=dato["moneda"],
            coberturas=[CoberturaVista.desde_nucleo(c) for c in dato["coberturas"]],
            datos_riesgo=[DatoRiesgoVista.desde_nucleo(d) for d in dato["datos_riesgo"]],
        )


class CatalogoVista(ModeloVista):
    productos: list[ProductoVista]


class ErrorVista(ModeloVista):
    codigo: str
    mensaje: str
