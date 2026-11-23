from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable, Sequence
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

    async def invalidar_consentimiento(self, consentimiento_id: str) -> None:
        """Descarta lo capturado bajo un consentimiento. Las entradas se indexan por
        cédula, que quien revoca no conoce; el consentimiento sí viaja en cada una."""
        for clave in [c for c, entrada in self._datos.items() if entrada.consentimiento_id == consentimiento_id]:
            del self._datos[clave]


class CacheFuentesConPurga(CacheEnMemoria):
    """Ademas de descartar lo de la memoria local, avisa a otros almacenes (la cache Redis
    compartida) para que borren lo capturado bajo un consentimiento revocado. Si una purga
    falla no se revierte la revocacion, que ya quedo persistida: se registra, y lo guardado
    vence solo al cumplirse su vigencia maxima."""

    def __init__(self, purgas: Sequence[Callable[[str], Awaitable[object]]]) -> None:
        super().__init__()
        self._purgas = list(purgas)

    async def invalidar_consentimiento(self, consentimiento_id: str) -> None:
        await super().invalidar_consentimiento(consentimiento_id)
        for purga in self._purgas:
            try:
                await purga(consentimiento_id)
            except Exception:
                logging.getLogger(__name__).warning("no se pudo purgar la cache compartida", exc_info=True)
