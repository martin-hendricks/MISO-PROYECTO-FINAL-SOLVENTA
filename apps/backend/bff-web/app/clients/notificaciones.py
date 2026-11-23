from __future__ import annotations

from typing import Any

from .base import ClienteServicio


class ClienteNotificaciones(ClienteServicio):
    """Cliente de notificaciones: audiencia con dispositivo y difusiones."""

    nombre = "notificaciones"

    async def audiencia(self, usuario_ids: list[str] | None = None) -> dict[str, Any]:
        """GET /v1/notificaciones/audiencia. `usuarioIds` se repite, hasta 50."""
        params = {"usuarioIds": usuario_ids} if usuario_ids else None
        return await self._pedir("GET", "/v1/notificaciones/audiencia", params=params)

    async def difundir(self, cuerpo: dict[str, Any]) -> dict[str, Any]:
        return await self._pedir("POST", "/v1/notificaciones/difusiones", json=cuerpo)

    async def historial(self, limite: int | None = None, antes_de: str | None = None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if limite is not None:
            params["limite"] = limite
        if antes_de:
            params["antesDe"] = antes_de
        return await self._pedir("GET", "/v1/notificaciones/difusiones", params=params or None)
