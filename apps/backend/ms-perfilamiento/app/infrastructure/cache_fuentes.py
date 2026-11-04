from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


@dataclass(frozen=True)
class EntradaCache:
    atributos: dict[str, Decimal]
    capturada_en: datetime
    consentimiento_id: str | None


class CacheEnMemoria:
    """Caché por fuente y cédula. Open Finance y Open Data no comparten entradas."""

    def __init__(self) -> None:
        self._datos: dict[tuple[str, str], EntradaCache] = {}

    async def obtener(self, fuente: str, numero_documento: str) -> EntradaCache | None:
        return self._datos.get((fuente, numero_documento))

    async def guardar(
        self,
        fuente: str,
        numero_documento: str,
        atributos: dict[str, Decimal],
        consentimiento_id: str | None = None,
    ) -> None:
        self._datos[(fuente, numero_documento)] = EntradaCache(
            atributos=dict(atributos),
            capturada_en=datetime.now(UTC),
            consentimiento_id=consentimiento_id,
        )

    async def invalidar(self, numero_documento: str) -> None:
        for clave in [clave for clave in self._datos if clave[1] == numero_documento]:
            del self._datos[clave]
