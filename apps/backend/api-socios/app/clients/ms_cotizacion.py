from __future__ import annotations

from typing import Any

from .base import ClienteServicio


class ClienteMsCotizacion(ClienteServicio):
    nombre = "ms-cotizacion"

    def __init__(self, http, correlacion: str | None = None, token: str = "") -> None:
        super().__init__(http, correlacion)
        self._token = token

    async def listar_productos(self) -> list[dict[str, Any]]:
        return await self._pedir("GET", "/v1/productos")

    async def obtener_producto(self, codigo: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/productos/{codigo}")

    async def cotizar(self, solicitud: dict[str, Any], idempotency_key: str) -> tuple[int, dict[str, Any]]:
        respuesta = await self._enviar(
            "POST",
            "/v1/cotizaciones",
            json=solicitud,
            cabeceras={"Authorization": f"Bearer {self._token}", "Idempotency-Key": idempotency_key},
        )
        return respuesta.status_code, respuesta.json()

    async def obtener_cotizacion(self, cotizacion_id: str) -> dict[str, Any]:
        return await self._pedir(
            "GET", f"/v1/cotizaciones/{cotizacion_id}", cabeceras={"Authorization": f"Bearer {self._token}"}
        )
