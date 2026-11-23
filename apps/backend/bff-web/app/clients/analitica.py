from __future__ import annotations

from datetime import date
from typing import Any

from .base import ClienteServicio


class ClienteAnalitica(ClienteServicio):
    """Cliente del servicio analitica (HU-68/69)."""

    nombre = "analitica"

    async def metricas(self, desde: date, hasta: date) -> dict[str, Any]:
        """HU-69: conteos agregados de eventos de ciclo de vida de póliza.

        El contenido lo define analitica (tipo/fecha/cantidad); bff-web solo
        reenvía la respuesta tal cual, sin interpretarla.
        """
        return await self._pedir(
            "GET",
            "/v1/metricas",
            params={"desde": desde.isoformat(), "hasta": hasta.isoformat()},
        )
