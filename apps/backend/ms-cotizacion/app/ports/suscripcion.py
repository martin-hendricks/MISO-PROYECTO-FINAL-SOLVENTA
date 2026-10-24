from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class DecisionSuscripcion:
    suscripcion_id: UUID
    decision: str
    motivo: str


class MotorSuscripcion(Protocol):
    async def evaluar(self, solicitud_id: UUID, perfil_id: UUID, score: Decimal) -> DecisionSuscripcion:
        """Decisión de HU-13 (ms-suscripcion). Es idempotente por solicitud: reintentar
        devuelve la decisión ya persistida."""
        ...
