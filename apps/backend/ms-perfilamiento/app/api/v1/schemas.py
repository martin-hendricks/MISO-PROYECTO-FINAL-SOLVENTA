from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import AtributoPerfil, Consentimiento, FactorInterno, Oferta, Originacion, OrigenOriginacion


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
    numero_documento: str | None = Field(default=None, min_length=1, max_length=50)


class AtributoPerfilSalida(BaseModel):
    nombre: str
    valor: Decimal
    origen: str
    estado: str
    degradado: bool
    modo: str = "LIVE"
    causa: str | None = None

    @classmethod
    def desde(cls, atributo: AtributoPerfil) -> "AtributoPerfilSalida":
        return cls(
            nombre=atributo.nombre,
            valor=atributo.valor,
            origen=atributo.origen.value,
            estado=atributo.estado.value,
            degradado=atributo.degradado,
            modo=atributo.modo,
            causa=atributo.causa.value if atributo.causa else None,
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
    factor_ajuste: Decimal
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
            factor_ajuste=oferta.factor_ajuste,
            factores=[FactorInternoSalida.desde(f) for f in oferta.factores],
            snapshot_atributos=[AtributoPerfilSalida.desde(a) for a in oferta.snapshot_atributos],
            creado_en=oferta.creado_en,
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str


class RegistrarOriginacionEntrada(BaseModel):
    cliente_id: str = Field(min_length=1, max_length=120)
    valor: Decimal = Field(gt=0)
    plazo_meses: int = Field(ge=1, le=480)
    origen: OrigenOriginacion = OrigenOriginacion.CLIENTE


class OriginacionSalida(BaseModel):
    id: UUID
    cliente_id: str
    valor: Decimal
    plazo_meses: int
    origen: OrigenOriginacion
    creada_en: datetime
    pendiente: bool

    @classmethod
    def desde(cls, originacion: Originacion) -> "OriginacionSalida":
        return cls(
            id=originacion.id,
            cliente_id=originacion.cliente_id,
            valor=originacion.valor,
            plazo_meses=originacion.plazo_meses,
            origen=originacion.origen,
            creada_en=originacion.creada_en,
            pendiente=originacion.pendiente,
        )
