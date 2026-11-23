from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import Pago


class CobrarPrimaEntrada(BaseModel):
    solicitud_id: UUID
    oferta_id: UUID
    usuario_id: UUID
    monto: Decimal = Field(max_digits=14, decimal_places=2)
    moneda: str
    token_medio_pago: str = Field(min_length=1, max_length=120)


class PagoSalida(BaseModel):
    id: UUID
    oferta_id: UUID
    monto: Decimal
    moneda: str
    estado: str
    idempotency_key: str
    referencia_externa: str
    fecha: datetime

    @classmethod
    def desde(cls, pago: Pago) -> "PagoSalida":
        return cls(
            id=pago.id,
            oferta_id=pago.oferta_id,
            monto=pago.monto,
            moneda=pago.moneda,
            estado=pago.estado.value,
            idempotency_key=pago.idempotency_key,
            referencia_externa=pago.referencia_externa,
            fecha=pago.fecha,
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
