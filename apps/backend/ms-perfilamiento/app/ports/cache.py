from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class PerfilGuardado:
    """Lo que la cache compartida conserva: los atributos y cuando se capturaron. La edad
    decide si el valor sigue fresco o solo sirve de respaldo; no decide si se descarta."""

    atributos: dict[str, Decimal]
    capturado_en: float


class CacheAtributos(Protocol):
    async def leer(self, clave: str) -> PerfilGuardado | None: ...

    async def guardar(
        self,
        clave: str,
        atributos: dict[str, Decimal],
        ttl_segundos: int,
        capturado_en: float,
        consentimiento_id: str | None = None,
    ) -> None: ...

    async def invalidar_consentimiento(self, consentimiento_id: str) -> int: ...
