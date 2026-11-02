from __future__ import annotations

from typing import Any
from uuid import UUID

from .base import ClienteServicio


class ClienteMsSiniestros(ClienteServicio):
    nombre = "ms-siniestros"

    async def listar(self, limite: int = 20) -> list[dict[str, Any]]:
        return await self._pedir("GET", "/v1/siniestros", params={"limite": limite})

    async def cambiar_estado(self, siniestro_id: UUID, estado: str, origen: str) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            f"/v1/siniestros/{siniestro_id}/estado",
            json={"estado": estado, "origen": origen},
        )

    async def abiertos_por_poliza(self, poliza_id: UUID) -> int:
        """HU-61: dato informativo para el operador antes de cancelar -- no
        bloquea la cancelación, ver operador.py."""
        cuerpo = await self._pedir("GET", "/v1/siniestros/abiertos", params={"poliza_id": str(poliza_id)})
        return int(cuerpo["abiertos"])
