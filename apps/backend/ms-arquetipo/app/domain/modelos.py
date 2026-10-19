from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada, TransicionInvalida


class EstadoEjemplo(StrEnum):
    REGISTRADO = "registrado"
    APROBADO = "aprobado"


@dataclass
class Ejemplo:
    id: UUID
    idempotency_key: str
    referencia: str
    monto: Decimal
    estado: EstadoEjemplo
    creado_en: datetime

    @classmethod
    def registrar(cls, idempotency_key: str, referencia: str, monto: Decimal) -> Ejemplo:
        if monto <= 0:
            raise ReglaDeNegocioViolada("monto_no_positivo", "El monto debe ser mayor que cero")
        if not referencia.strip():
            raise ReglaDeNegocioViolada("referencia_vacia", "La referencia es obligatoria")
        return cls(
            id=uuid4(),
            idempotency_key=idempotency_key,
            referencia=referencia.strip(),
            monto=monto,
            estado=EstadoEjemplo.REGISTRADO,
            creado_en=datetime.now(UTC),
        )

    def aprobar(self) -> None:
        if self.estado is not EstadoEjemplo.REGISTRADO:
            raise TransicionInvalida(self.estado, EstadoEjemplo.APROBADO)
        self.estado = EstadoEjemplo.APROBADO


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    agregado_id: UUID
    payload: dict
    id: UUID = field(default_factory=uuid4)


def ejemplo_registrado(ejemplo: Ejemplo) -> EventoDominio:
    return EventoDominio(
        tipo="EjemploRegistrado",
        agregado_id=ejemplo.id,
        payload={"id": str(ejemplo.id), "referencia": ejemplo.referencia, "monto": str(ejemplo.monto)},
    )


def ejemplo_aprobado(ejemplo: Ejemplo) -> EventoDominio:
    return EventoDominio(tipo="EjemploAprobado", agregado_id=ejemplo.id, payload={"id": str(ejemplo.id)})
