from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.application.casos_uso import ResultadoIngesta
from app.domain.modelos import EstadoSiniestro, Siniestro


class EventoParametricoEntrada(BaseModel):
    evento_id: str = Field(min_length=1, max_length=120)
    valor: Decimal = Field(max_digits=18, decimal_places=4)
    umbral: Decimal = Field(max_digits=18, decimal_places=4)
    poliza_vigente: bool = True
    monto_pago: Decimal = Field(max_digits=14, decimal_places=2, gt=0)


class TransicionSalida(BaseModel):
    estado: str
    ocurrido_en: datetime
    origen: str


class SiniestroSalida(BaseModel):
    id: UUID
    evento_id: str
    estado: str
    creado_en: datetime
    historial: list[TransicionSalida]

    @classmethod
    def desde(cls, siniestro: Siniestro) -> "SiniestroSalida":
        return cls(
            id=siniestro.id,
            evento_id=siniestro.evento_id,
            estado=siniestro.estado.value,
            creado_en=siniestro.creado_en,
            historial=[
                TransicionSalida(estado=t.estado.value, ocurrido_en=t.ocurrido_en, origen=t.origen)
                for t in siniestro.historial
            ],
        )


class EvaluacionSalida(BaseModel):
    evento_id: str
    umbral: Decimal
    valor: Decimal
    poliza_vigente: bool
    decision: bool
    motivo: str
    evaluada_en: datetime


class PagoSalida(BaseModel):
    evento_id: str
    siniestro_id: UUID
    monto: Decimal
    pagado_en: datetime


class ResultadoIngestaSalida(BaseModel):
    siniestro: SiniestroSalida
    evaluacion: EvaluacionSalida
    pago: PagoSalida | None
    procesado: bool

    @classmethod
    def desde(cls, resultado: ResultadoIngesta) -> "ResultadoIngestaSalida":
        return cls(
            siniestro=SiniestroSalida.desde(resultado.siniestro),
            evaluacion=EvaluacionSalida(
                evento_id=resultado.evaluacion.evento_id,
                umbral=resultado.evaluacion.umbral,
                valor=resultado.evaluacion.valor,
                poliza_vigente=resultado.evaluacion.poliza_vigente,
                decision=resultado.evaluacion.decision,
                motivo=resultado.evaluacion.motivo,
                evaluada_en=resultado.evaluacion.evaluada_en,
            ),
            pago=(
                PagoSalida(
                    evento_id=resultado.pago.evento_id,
                    siniestro_id=resultado.pago.siniestro_id,
                    monto=resultado.pago.monto,
                    pagado_en=resultado.pago.pagado_en,
                )
                if resultado.pago is not None
                else None
            ),
            procesado=resultado.procesado,
        )


class CambiarEstadoEntrada(BaseModel):
    estado: EstadoSiniestro
    origen: str = Field(min_length=1, max_length=120)


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
