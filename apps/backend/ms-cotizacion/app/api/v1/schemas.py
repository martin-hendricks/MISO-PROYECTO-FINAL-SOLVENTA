from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.domain.modelos import Cotizacion


class Contrato(BaseModel):
    """Contrato de cotización en camelCase, como el de socios y BFF (wiki Contratos-BFF)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SolicitudCotizacionEntrada(Contrato):
    producto: str = Field(min_length=1, max_length=64, examples=["PROTECCION_DISPOSITIVO"])
    # Varía con el producto: la valida el catálogo, no el esquema HTTP.
    datos_riesgo: dict[str, Any] = Field(
        examples=[{"valorDispositivo": 2400000, "marca": "Pixel", "masDe12Meses": False}]
    )


class CoberturaSalida(Contrato):
    codigo: str
    nombre: str
    limite: Decimal


class CotizacionSalida(Contrato):
    cotizacion_id: UUID
    producto: str
    estado: str
    prima: Decimal
    moneda: str
    coberturas: list[CoberturaSalida]
    vence_en: datetime

    @classmethod
    def desde(cls, cotizacion: Cotizacion) -> "CotizacionSalida":
        return cls(
            cotizacion_id=cotizacion.id,
            producto=cotizacion.producto,
            estado=cotizacion.estado.value,
            prima=cotizacion.prima,
            moneda=cotizacion.moneda,
            coberturas=[CoberturaSalida(codigo=c.codigo, nombre=c.nombre, limite=c.limite) for c in cotizacion.coberturas],
            vence_en=cotizacion.vence_en,
        )


class ErrorSalida(Contrato):
    codigo: str
    mensaje: str
    campo: str | None = None
    rango_valido: dict | None = None
