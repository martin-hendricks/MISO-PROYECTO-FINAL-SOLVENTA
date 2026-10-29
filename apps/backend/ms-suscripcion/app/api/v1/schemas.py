from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import Suscripcion


class EvaluarSuscripcionEntrada(BaseModel):
    solicitud_id: UUID
    perfil_id: UUID
    score: Decimal = Field(ge=0, max_digits=10, decimal_places=4)


class SuscripcionSalida(BaseModel):
    suscripcion_id: UUID
    solicitud_id: UUID
    perfil_id: UUID
    decision: str
    motivo: str
    regla: str
    evaluada_en: datetime

    @classmethod
    def desde(cls, suscripcion: Suscripcion) -> "SuscripcionSalida":
        return cls(
            suscripcion_id=suscripcion.id,
            solicitud_id=suscripcion.solicitud_id,
            perfil_id=suscripcion.perfil_id,
            decision=suscripcion.decision.value,
            motivo=suscripcion.motivo,
            regla=suscripcion.regla,
            evaluada_en=suscripcion.evaluada_en,
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
