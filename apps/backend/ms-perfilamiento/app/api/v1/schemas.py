from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import AtributoPerfil, Consentimiento, FactorInterno, Oferta


class OtorgarConsentimientoEntrada(BaseModel):
    cliente_id: str = Field(min_length=1, max_length=120)


class ConsentimientoSalida(BaseModel):
    id: UUID
    cliente_id: str
    otorgado_en: datetime
    revocado_en: datetime | None
    vigente: bool

    @classmethod
    def desde(cls, consentimiento: Consentimiento) -> "ConsentimientoSalida":
        return cls(
            id=consentimiento.id,
            cliente_id=consentimiento.cliente_id,
            otorgado_en=consentimiento.otorgado_en,
            revocado_en=consentimiento.revocado_en,
            vigente=consentimiento.vigente,
        )


class SolicitarOfertaEntrada(BaseModel):
    cliente_id: str = Field(min_length=1, max_length=120)


class AtributoPerfilSalida(BaseModel):
    nombre: str
    valor: Decimal
    origen: str
    estado: str
    degradado: bool

    @classmethod
    def desde(cls, atributo: AtributoPerfil) -> "AtributoPerfilSalida":
        return cls(
            nombre=atributo.nombre,
            valor=atributo.valor,
            origen=atributo.origen.value,
            estado=atributo.estado.value,
            degradado=atributo.degradado,
        )


class FactorInternoSalida(BaseModel):
    factor: str
    impacto: str
    peso: Decimal

    @classmethod
    def desde(cls, factor: FactorInterno) -> "FactorInternoSalida":
        return cls(factor=factor.factor, impacto=factor.impacto, peso=factor.peso)


class OfertaSalida(BaseModel):
    id: UUID
    cliente_id: str
    precio: Decimal
    moneda: str
    degradado: bool
    factores: list[FactorInternoSalida]
    snapshot_atributos: list[AtributoPerfilSalida]
    creado_en: datetime

    @classmethod
    def desde(cls, oferta: Oferta) -> "OfertaSalida":
        return cls(
            id=oferta.id,
            cliente_id=oferta.cliente_id,
            precio=oferta.precio,
            moneda=oferta.moneda,
            degradado=oferta.degradado,
            factores=[FactorInternoSalida.desde(f) for f in oferta.factores],
            snapshot_atributos=[AtributoPerfilSalida.desde(a) for a in oferta.snapshot_atributos],
            creado_en=oferta.creado_en,
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
