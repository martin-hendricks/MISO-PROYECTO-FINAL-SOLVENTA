from __future__ import annotations

from typing import Any
from uuid import UUID

from .base import ClienteServicio


class ClienteMsPolizas(ClienteServicio):
    """Cliente de ms-polizas."""

    nombre = "ms-polizas"

    async def emitir(
        self,
        solicitud_id: UUID,
        oferta_id: UUID,
        usuario_id: UUID,
        token_pago_confirmado: UUID,
        coberturas: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            "/v1/polizas",
            json={
                "solicitud_id": str(solicitud_id),
                "oferta_id": str(oferta_id),
                "usuario_id": str(usuario_id),
                "token_pago_confirmado": str(token_pago_confirmado),
                "coberturas": coberturas,
            },
        )

    async def obtener(self, poliza_id: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/polizas/{poliza_id}")

    async def listar_por_usuario(self, usuario_id: UUID, limite: int) -> list[dict[str, Any]]:
        return await self._pedir(
            "GET", "/v1/polizas", params={"usuario_id": str(usuario_id), "limite": limite}
        )

    async def obtener_por_numero(self, numero: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/polizas/numero/{numero}")
