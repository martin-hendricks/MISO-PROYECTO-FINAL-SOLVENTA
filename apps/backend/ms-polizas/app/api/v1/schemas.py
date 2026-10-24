from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import Cobertura, Poliza


class CoberturaEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    suma_asegurada: Decimal = Field(max_digits=14, decimal_places=2)
    deducible: Decimal = Field(default=Decimal("0"), max_digits=14, decimal_places=2)

    def a_dominio(self) -> Cobertura:
        return Cobertura(nombre=self.nombre, suma_asegurada=self.suma_asegurada, deducible=self.deducible)


class EmitirPolizaEntrada(BaseModel):
    solicitud_id: UUID
    oferta_id: UUID
    usuario_id: UUID
    token_pago_confirmado: UUID
    coberturas: list[CoberturaEntrada] = Field(min_length=1)


class CoberturaSalida(BaseModel):
    nombre: str
    suma_asegurada: Decimal
    deducible: Decimal


class PolizaSalida(BaseModel):
    id: UUID
    numero: str
    oferta_id: UUID
    usuario_id: UUID
    inicio_vigencia: date
    fin_vigencia: date
    estado: str
    coberturas: list[CoberturaSalida]

    @classmethod
    def desde(cls, poliza: Poliza) -> "PolizaSalida":
        return cls(
            id=poliza.id,
            numero=poliza.numero,
            oferta_id=poliza.oferta_id,
            usuario_id=poliza.usuario_id,
            inicio_vigencia=poliza.inicio_vigencia,
            fin_vigencia=poliza.fin_vigencia,
            estado=poliza.estado.value,
            coberturas=[
                CoberturaSalida(nombre=c.nombre, suma_asegurada=c.suma_asegurada, deducible=c.deducible)
                for c in poliza.coberturas
            ],
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
