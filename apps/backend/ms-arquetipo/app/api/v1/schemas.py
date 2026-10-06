from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import Ejemplo


class RegistrarEjemploEntrada(BaseModel):
    referencia: str = Field(min_length=1, max_length=120)
    monto: Decimal = Field(max_digits=14, decimal_places=2)


class EjemploSalida(BaseModel):
    id: UUID
    referencia: str
    monto: Decimal
    estado: str
    creado_en: datetime

    @classmethod
    def desde(cls, ejemplo: Ejemplo) -> "EjemploSalida":
        return cls(
            id=ejemplo.id,
            referencia=ejemplo.referencia,
            monto=ejemplo.monto,
            estado=ejemplo.estado.value,
            creado_en=ejemplo.creado_en,
        )


class IndicadoresSalida(BaseModel):
    total: int
    monto_total: Decimal


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
