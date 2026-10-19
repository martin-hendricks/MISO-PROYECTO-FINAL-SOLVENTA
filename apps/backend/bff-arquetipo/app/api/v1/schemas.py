from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class ModeloVista(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, extra="ignore")


class EjemploVista(ModeloVista):
    id: str
    referencia: str
    monto: Decimal
    moneda: str = "COP"
    estado: str
    creado_en: str

    @classmethod
    def desde_nucleo(cls, dato: dict) -> EjemploVista:
        return cls(
            id=dato["id"],
            referencia=dato["referencia"],
            monto=Decimal(str(dato["monto"])),
            estado=dato["estado"],
            creado_en=dato["creado_en"],
        )


class IndicadoresVista(ModeloVista):
    total: int
    monto_total: Decimal


class InicioVista(ModeloVista):
    ejemplos: list[EjemploVista]
    indicadores: IndicadoresVista | None = None
    degradado: list[str] = Field(default_factory=list)


class RegistrarEjemploEntrada(ModeloVista):
    referencia: str = Field(min_length=1, max_length=120)
    monto: Decimal = Field(gt=0, max_digits=14, decimal_places=2)


class ErrorVista(ModeloVista):
    codigo: str
    mensaje: str
