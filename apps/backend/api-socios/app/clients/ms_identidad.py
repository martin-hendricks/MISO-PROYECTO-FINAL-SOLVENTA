from __future__ import annotations

from .base import ClienteServicio


class ClienteMsIdentidad(ClienteServicio):
    nombre = "ms-identidad"

    def __init__(self, http, correlacion: str | None = None, token: str = "") -> None:
        super().__init__(http, correlacion)
        self._token = token

    async def usuario_por_documento(self, tipo_documento: str, numero_documento: str) -> str:
        datos = await self._pedir(
            "GET",
            "/v1/usuarios/documento",
            params={"tipo_documento": tipo_documento, "numero_documento": numero_documento},
            cabeceras={"Authorization": f"Bearer {self._token}"},
        )
        return str(datos["usuario_id"])
