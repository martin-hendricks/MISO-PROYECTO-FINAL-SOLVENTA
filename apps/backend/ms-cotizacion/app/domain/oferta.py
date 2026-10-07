from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

from .modelos import EventoDominio, SolicitudCotizacion
from .rating import ReglaRating, ResultadoPrima
from .riesgo import FactorRiesgo, OrigenFactorRiesgo


@dataclass
class Oferta:
    id: UUID
    solicitud_id: UUID
    regla_id: UUID
    version_regla: str
    prima_neta: Decimal
    gastos_expedicion: Decimal
    moneda: str
    coberturas: list[str]
    factor_riesgo: Decimal
    factor_riesgo_origen: OrigenFactorRiesgo
    vence_en: datetime

    @property
    def prima(self) -> Decimal:
        return self.prima_neta + self.gastos_expedicion

    @classmethod
    def emitir(
        cls,
        solicitud: SolicitudCotizacion,
        regla: ReglaRating,
        resultado: ResultadoPrima,
        factor: FactorRiesgo,
        coberturas: list[str],
        vigencia: timedelta,
    ) -> Oferta:
        ahora = datetime.now(UTC)
        return cls(
            id=uuid4(),
            solicitud_id=solicitud.id,
            regla_id=regla.id,
            version_regla=regla.version,
            prima_neta=resultado.prima_neta,
            gastos_expedicion=resultado.gastos_expedicion,
            moneda=resultado.moneda,
            coberturas=coberturas,
            factor_riesgo=factor.valor,
            factor_riesgo_origen=factor.origen,
            vence_en=ahora + vigencia,
        )

    def vigente(self, ahora: datetime | None = None) -> bool:
        return (ahora or datetime.now(UTC)) < self.vence_en


def oferta_emitida(oferta: Oferta) -> EventoDominio:
    return EventoDominio(
        tipo="OfertaEmitida",
        agregado_id=oferta.id,
        payload={
            "oferta_id": str(oferta.id),
            "solicitud_id": str(oferta.solicitud_id),
            "prima": str(oferta.prima),
            "moneda": oferta.moneda,
            "factor_riesgo_origen": oferta.factor_riesgo_origen.value,
        },
    )
