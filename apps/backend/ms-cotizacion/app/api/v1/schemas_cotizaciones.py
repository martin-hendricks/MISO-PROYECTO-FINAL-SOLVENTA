from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import SolicitudCotizacion
from app.domain.oferta import ConsultaOferta, Oferta


class SolicitarCotizacionEntrada(BaseModel):
    usuario_id: UUID
    socio_id: UUID
    consentimiento_id: UUID
    producto: str = Field(min_length=1, max_length=80)
    canal: str = Field(min_length=1, max_length=40)
    datos_riesgo: dict[str, Any] = Field(default_factory=dict)


class CotizacionSalida(BaseModel):
    cotizacion_id: UUID
    estado: str
    producto: str
    creada_en: datetime
    prima: Decimal
    prima_neta: Decimal
    gastos_expedicion: Decimal
    moneda: str
    vence_en: datetime
    factor_riesgo_origen: str
    vencida: bool = False

    @classmethod
    def desde(cls, solicitud: SolicitudCotizacion, oferta: Oferta) -> "CotizacionSalida":
        return cls(
            cotizacion_id=solicitud.id,
            estado=solicitud.estado.value,
            producto=solicitud.producto,
            creada_en=solicitud.creada_en,
            prima=oferta.prima,
            prima_neta=oferta.prima_neta,
            gastos_expedicion=oferta.gastos_expedicion,
            moneda=oferta.moneda,
            vence_en=oferta.vence_en,
            factor_riesgo_origen=oferta.factor_riesgo_origen.value,
        )

    @classmethod
    def desde_consulta(cls, solicitud: SolicitudCotizacion, consulta: ConsultaOferta) -> "CotizacionSalida":
        base = cls.desde(solicitud, consulta.oferta)
        return base.model_copy(update={"vencida": consulta.vencida})


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
