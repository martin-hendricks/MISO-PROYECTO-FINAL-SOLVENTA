"""Proveedor simulado de clima: reporta la precipitación acumulada de una estación."""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.evento import EventoTelemetria

from ._comun import CoberturaProveedor, validar


class MedicionPrecipitacion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    medicion_id: str = Field(min_length=1, max_length=80)
    estacion: str = Field(min_length=1, max_length=40)
    precipitacion_mm: Decimal = Field(ge=0, max_digits=8, decimal_places=2)
    medido_en: datetime
    cobertura: CoberturaProveedor


class AdaptadorClima:
    proveedor = "clima"

    def traducir(self, carga: dict) -> EventoTelemetria:
        medicion = validar(MedicionPrecipitacion, carga, self.proveedor)
        return EventoTelemetria(
            evento_id=EventoTelemetria.clave(self.proveedor, medicion.medicion_id),
            proveedor=self.proveedor,
            tipo="precipitacion",
            valor=medicion.precipitacion_mm,
            ocurrido_en=medicion.medido_en,
            ramo="clima-vuelos",
            descripcion=f"Precipitación en {medicion.estacion}: {medicion.precipitacion_mm} mm",
            cobertura=medicion.cobertura.a_dominio(),
        )
