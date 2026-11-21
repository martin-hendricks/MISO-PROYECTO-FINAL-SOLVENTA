from __future__ import annotations

from typing import Any

from .base import ClienteServicio, RecursoNoEncontrado


class ClienteMsPerfilamiento(ClienteServicio):
    nombre = "ms-perfilamiento"

    def __init__(self, http, correlacion: str | None = None, token: str = "") -> None:
        super().__init__(http, correlacion)
        self._token = token

    async def consentimiento_vigente(self, cliente_id: str) -> str | None:
        try:
            datos = await self._pedir(
                "GET", f"/v1/consentimientos/{cliente_id}", cabeceras={"Authorization": f"Bearer {self._token}"}
            )
        except RecursoNoEncontrado:
            return None
        return str(datos["id"]) if datos.get("vigente") is True else None

    async def registrar_originacion(self, cliente_id: str, valor: int, plazo_meses: int) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            "/v1/originaciones",
            json={"cliente_id": cliente_id, "valor": str(valor), "plazo_meses": plazo_meses, "origen": "socio"},
            cabeceras={"Authorization": f"Bearer {self._token}"},
        )
