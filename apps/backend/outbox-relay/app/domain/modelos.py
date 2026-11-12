from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

# Envelope publicado en BusEventos. El contrato es fijo: los consumidores
# (notificaciones, analitica) deduplican por `evento_id` y ordenan por
# agregado usando la key del mensaje, así que estas seis claves no cambian.
CAMPOS_MENSAJE = (
    "evento_id",
    "tipo",
    "agregado_id",
    "ocurrido_en",
    "origen",
    "payload",
)


@dataclass(frozen=True)
class EventoOutbox:
    evento_id: UUID
    esquema: str
    tipo: str
    agregado_id: UUID
    payload: dict
    creado_en: datetime

    def a_mensaje(self) -> dict:
        return {
            "evento_id": str(self.evento_id),
            "tipo": self.tipo,
            "agregado_id": str(self.agregado_id),
            "ocurrido_en": _iso_utc(self.creado_en),
            "origen": self.esquema,
            "payload": self.payload,
        }

    def clave(self) -> str:
        # Key por agregado: Kafka garantiza orden dentro de una partición, y
        # con la misma key todos los eventos de un agregado caen en la misma.
        return str(self.agregado_id)


def _iso_utc(valor: datetime) -> str:
    # asyncpg devuelve TIMESTAMPTZ con tzinfo, pero un datetime naive se
    # interpreta como UTC en vez de reventar en astimezone().
    instante = valor.replace(tzinfo=UTC) if valor.tzinfo is None else valor
    return instante.astimezone(UTC).isoformat()
