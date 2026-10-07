from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID, uuid4


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    agregado_id: UUID
    payload: dict
    id: UUID = field(default_factory=uuid4)
