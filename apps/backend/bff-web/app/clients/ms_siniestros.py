from __future__ import annotations

from typing import Any
from uuid import UUID

from .base import ClienteServicio, RechazoDelNucleo, RecursoNoEncontrado, ServicioNoDisponible


class ClienteMsSiniestros(ClienteServicio):
    nombre = "ms-siniestros"

    async def listar(self, limite: int = 20, usuario_id: UUID | None = None) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"limite": limite}
        if usuario_id is not None:
            params["usuario_id"] = str(usuario_id)
        return await self._pedir("GET", "/v1/siniestros", params=params)

    async def cambiar_estado(self, siniestro_id: UUID, estado: str, origen: str) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            f"/v1/siniestros/{siniestro_id}/estado",
            json={"estado": estado, "origen": origen},
        )

    async def abiertos_por_poliza(self, poliza_id: UUID) -> int | None:
        """HU-61: dato informativo. Si el servicio no responde, la cancelación sigue."""
        try:
            cuerpo = await self._pedir("GET", "/v1/siniestros/abiertos", params={"poliza_id": str(poliza_id)})
            return int(cuerpo["abiertos"])
        except (ServicioNoDisponible, RecursoNoEncontrado, RechazoDelNucleo, KeyError, TypeError, ValueError):
            return None
