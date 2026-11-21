"""Proveedor simulado de estado de vuelos: reporta el retraso de un vuelo en minutos."""

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.evento import EventoTelemetria

from ._comun import CoberturaProveedor, validar


class ReporteRetrasoVuelo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reporte_id: str = Field(min_length=1, max_length=80)
    vuelo: str = Field(min_length=2, max_length=10)
    fecha: date
    retraso_minutos: int = Field(ge=0, le=7 * 24 * 60)
    reportado_en: datetime
    cobertura: CoberturaProveedor


class AdaptadorVuelos:
    proveedor = "vuelos"

    def traducir(self, carga: dict) -> EventoTelemetria:
        reporte = validar(ReporteRetrasoVuelo, carga, self.proveedor)
        return EventoTelemetria(
            evento_id=EventoTelemetria.clave(self.proveedor, reporte.reporte_id),
            proveedor=self.proveedor,
            tipo="retraso_vuelo",
            valor=Decimal(reporte.retraso_minutos),
            ocurrido_en=reporte.reportado_en,
            ramo="clima-vuelos",
            descripcion=f"Retraso del vuelo {reporte.vuelo.upper()} del {reporte.fecha.isoformat()}: "
            f"{reporte.retraso_minutos} min",
            cobertura=reporte.cobertura.a_dominio(),
        )
