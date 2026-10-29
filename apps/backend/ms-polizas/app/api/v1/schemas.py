from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import Cobertura, ConstanciaFirma, Poliza


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


class OfertasConPolizaSalida(BaseModel):
    oferta_ids_con_poliza: list[UUID]


class PolizaSalida(BaseModel):
    id: UUID
    numero: str
    oferta_id: UUID
    usuario_id: UUID
    inicio_vigencia: date
    fin_vigencia: date
    estado: str
    coberturas: list[CoberturaSalida]
    motivo_cancelacion: str | None = None
    cancelada_en: date | None = None
    hash_firma_legal: str | None = None

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
            motivo_cancelacion=poliza.motivo_cancelacion,
            cancelada_en=poliza.cancelada_en,
            hash_firma_legal=poliza.firma_hash,
        )


class ConstanciaFirmaSalida(BaseModel):
    oferta_id: UUID
    resultado: str
    motivo: str | None
    firma_hash: str | None
    firmada_en: datetime

    @classmethod
    def desde(cls, constancia: ConstanciaFirma) -> "ConstanciaFirmaSalida":
        return cls(
            oferta_id=constancia.oferta_id,
            resultado="OK" if constancia.exitosa else "NO",
            motivo=constancia.motivo,
            firma_hash=constancia.firma_hash,
            firmada_en=constancia.firmada_en,
        )


class RenovarPolizaEntrada(BaseModel):
    nueva_fin_vigencia: date


class ModificarCoberturasEntrada(BaseModel):
    coberturas: list[CoberturaEntrada] = Field(min_length=1)


class CancelarPolizaEntrada(BaseModel):
    motivo: str = Field(min_length=1)


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
