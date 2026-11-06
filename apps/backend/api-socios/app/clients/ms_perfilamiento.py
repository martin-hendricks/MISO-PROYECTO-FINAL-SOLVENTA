from __future__ import annotations

from typing import Any

from .base import ClienteServicio


class ClienteMsPerfilamiento(ClienteServicio):
    nombre = "ms-perfilamiento"

    async def registrar_originacion(self, cliente_id: str, valor: int, plazo_meses: int) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            "/v1/originaciones",
            json={"cliente_id": cliente_id, "valor": str(valor), "plazo_meses": plazo_meses, "origen": "socio"},
        )
