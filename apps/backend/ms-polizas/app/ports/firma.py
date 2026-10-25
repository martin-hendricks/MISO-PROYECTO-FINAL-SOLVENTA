from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True)
class ResultadoFirma:
    exitosa: bool
    motivo: str | None = None
    firma_hash: str | None = None


class FirmaElectronica(Protocol):
    """Firma la emisión de una oferta (HU-17). Hoy la implementa un stub; un
    prestador real solo necesita otro adaptador con este mismo contrato."""

    async def firmar(self, oferta_id: UUID) -> ResultadoFirma: ...
