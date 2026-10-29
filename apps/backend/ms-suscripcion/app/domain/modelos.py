from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada


class Decision(StrEnum):
    ACEPTADA = "ACEPTADA"
    RECHAZADA = "RECHAZADA"


@dataclass(frozen=True)
class ReglaSuscripcion:
    """Regla de aceptación de riesgo como dato (EC-MOD-04): vive en la tabla
    regla_suscripcion y cambiarla no exige tocar código. Un score menor o igual a
    score_maximo está dentro del apetito de riesgo."""

    id: UUID
    score_maximo: Decimal
    motivo_aceptacion: str
    motivo_rechazo: str

    @property
    def descripcion(self) -> str:
        return f"Score de riesgo hasta {self.score_maximo}"

    def evaluar(self, score: Decimal) -> tuple[Decision, str]:
        if score <= self.score_maximo:
            return Decision.ACEPTADA, self.motivo_aceptacion
        return Decision.RECHAZADA, self.motivo_rechazo


@dataclass
class Suscripcion:
    id: UUID
    solicitud_id: UUID
    perfil_id: UUID
    decision: Decision
    motivo: str
    evaluada_en: datetime
    # Copia de la regla que aplicó: la decisión sigue siendo auditable aunque
    # la regla vigente cambie después (HU-149 muestra "la regla aplicada").
    regla: str = ""

    @classmethod
    def decidir(cls, solicitud_id: UUID, perfil_id: UUID, score: Decimal, regla: ReglaSuscripcion) -> Suscripcion:
        if score < 0:
            raise ReglaDeNegocioViolada("score_negativo", "El score de riesgo no puede ser negativo")
        decision, motivo = regla.evaluar(score)
        return cls(
            id=uuid4(),
            solicitud_id=solicitud_id,
            perfil_id=perfil_id,
            decision=decision,
            motivo=motivo,
            evaluada_en=datetime.now(UTC),
            regla=regla.descripcion,
        )

    @property
    def aceptada(self) -> bool:
        return self.decision is Decision.ACEPTADA


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    agregado_id: UUID
    payload: dict
    id: UUID = field(default_factory=uuid4)


def suscripcion_decidida(suscripcion: Suscripcion) -> EventoDominio:
    return EventoDominio(
        tipo="SuscripcionDecidida",
        agregado_id=suscripcion.id,
        payload={
            "suscripcion_id": str(suscripcion.id),
            "solicitud_id": str(suscripcion.solicitud_id),
            "perfil_id": str(suscripcion.perfil_id),
            "decision": suscripcion.decision.value,
            "motivo": suscripcion.motivo,
            "evaluada_en": suscripcion.evaluada_en.isoformat(),
        },
    )
