from __future__ import annotations

from typing import Any

from .base import ClienteServicio


class ClienteMsCotizacion(ClienteServicio):
    nombre = "ms-cotizacion"

    async def listar_productos(self) -> list[dict[str, Any]]:
        return await self._pedir("GET", "/v1/productos")

    async def obtener_producto(self, codigo: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/productos/{codigo}")
