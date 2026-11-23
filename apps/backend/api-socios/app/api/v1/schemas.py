from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ModeloVista(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


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
    tipo: Literal["rango", "valores", "texto", "booleano"]
    minimo: Decimal | None = None
    maximo: Decimal | None = None
    valores: list[str] | None = None

    @classmethod
    def desde_nucleo(cls, dato: dict) -> DatoRiesgoVista:
        tipo = dato["tipo"]
        nombre = dato["nombre"]
        if tipo == "rango":
            return cls(
                nombre=nombre,
                tipo="rango",
                minimo=Decimal(str(dato["minimo"])),
                maximo=Decimal(str(dato["maximo"])),
            )
        if tipo == "valores":
            return cls(nombre=nombre, tipo="valores", valores=list(dato["valores"]))
        if tipo in ("texto", "booleano"):
            return cls(nombre=nombre, tipo=tipo)
        raise ValueError(f"Tipo de dato de riesgo desconocido '{tipo}'")


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


class OriginacionEntrada(ModeloVista):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    tipo_documento: str = Field(min_length=1, max_length=10)
    numero_documento: str = Field(min_length=1, max_length=50)
    valor: int = Field(gt=0)
    plazo_meses: int = Field(ge=1, le=480)


class OriginacionVista(ModeloVista):
    estado: Literal["pendiente"] = "pendiente"
    valor: int
    plazo_meses: int


class CotizacionEntrada(ModeloVista):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="forbid")

    tipo_documento: str = Field(min_length=1, max_length=10)
    numero_documento: str = Field(min_length=1, max_length=50)
    producto: str = Field(min_length=1, max_length=80)
    datos_riesgo: dict[str, Any]


class CotizacionVista(ModeloVista):
    cotizacion_id: str
    estado: str
    producto: str
    prima: str
    prima_neta: str
    gastos_expedicion: str
    moneda: str
    vence_en: str
    vencida: bool = False
    consentimiento_pendiente: bool | None = None

    @classmethod
    def desde_nucleo(cls, datos: dict[str, Any], consentimiento_pendiente: bool | None = None) -> "CotizacionVista":
        return cls(
            cotizacion_id=str(datos["cotizacion_id"]),
            estado=str(datos["estado"]),
            producto=str(datos["producto"]),
            prima=str(datos["prima"]),
            prima_neta=str(datos["prima_neta"]),
            gastos_expedicion=str(datos["gastos_expedicion"]),
            moneda=str(datos["moneda"]),
            vence_en=str(datos["vence_en"]),
            vencida=bool(datos.get("vencida", False)),
            consentimiento_pendiente=consentimiento_pendiente,
        )
