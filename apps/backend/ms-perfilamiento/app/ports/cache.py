from __future__ import annotations

from decimal import Decimal
from typing import Protocol


class CacheAtributos(Protocol):
    async def leer(self, clave: str) -> dict[str, Decimal] | None: ...

    async def guardar(self, clave: str, atributos: dict[str, Decimal], ttl_segundos: int) -> None: ...
