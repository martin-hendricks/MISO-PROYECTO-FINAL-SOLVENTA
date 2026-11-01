from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada

CONCEPTO_PRIMA = "PRIMA"


class EstadoPago(StrEnum):
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


def clave_cobro_prima(oferta_id: UUID) -> str:
    """La clave se deriva de la operación (una prima por oferta), no se genera al azar en cada intento."""
    return f"cobro-prima:{oferta_id}"


@dataclass(frozen=True)
class ResultadoPasarela:
    estado: EstadoPago
    proveedor: str
    referencia_externa: str


@dataclass
class Pago:
    id: UUID
    oferta_id: UUID
    usuario_id: UUID
    monto: Decimal
    estado: EstadoPago
    idempotency_key: str
    proveedor: str
    referencia_externa: str
    fecha: datetime

    @staticmethod
    def validar_monto(monto: Decimal) -> None:
        if monto <= 0:
            raise ReglaDeNegocioViolada("monto_no_positivo", "El monto de la prima debe ser mayor que cero")

    @classmethod
    def registrar_prima(
        cls, oferta_id: UUID, usuario_id: UUID, monto: Decimal, resultado: ResultadoPasarela
    ) -> Pago:
        cls.validar_monto(monto)
        return cls(
            id=uuid4(),
            oferta_id=oferta_id,
            usuario_id=usuario_id,
            monto=monto,
            estado=resultado.estado,
            idempotency_key=clave_cobro_prima(oferta_id),
            proveedor=resultado.proveedor,
            referencia_externa=resultado.referencia_externa,
            fecha=datetime.now(UTC),
        )


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    agregado_id: UUID
    payload: dict
    id: UUID = field(default_factory=uuid4)


def pago_prima_registrado(pago: Pago) -> EventoDominio:
    return EventoDominio(
        tipo="PagoPrimaRegistrado",
        agregado_id=pago.id,
        payload={
            "pago_id": str(pago.id),
            "oferta_id": str(pago.oferta_id),
            "monto": str(pago.monto),
            "estado": pago.estado.value,
        },
    )
