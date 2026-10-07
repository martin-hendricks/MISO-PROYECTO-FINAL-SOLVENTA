from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import SolicitudCotizacion


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

    @classmethod
    def desde(cls, solicitud: SolicitudCotizacion) -> "CotizacionSalida":
        return cls(
            cotizacion_id=solicitud.id,
            estado=solicitud.estado.value,
            producto=solicitud.producto,
            creada_en=solicitud.creada_en,
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
