from __future__ import annotations

from typing import Any

from .base import ClienteServicio


class ClienteMsPerfilamiento(ClienteServicio):
    nombre = "ms-perfilamiento"

    async def otorgar_consentimiento(self, cliente_id: str) -> dict[str, Any]:
        """POST /v1/consentimientos. Idempotente del lado de ms-perfilamiento:
        si el cliente ya tiene un consentimiento vigente, el servicio responde
        200 (en vez de 201) con el registro existente en lugar de duplicarlo."""
        return await self._pedir(
            "POST",
            "/v1/consentimientos",
            json={"cliente_id": cliente_id},
        )

    async def solicitar_oferta_hipotecario(self, idempotency_key: str, cliente_id: str) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            "/v1/ofertas-hipotecario",
            json={"cliente_id": cliente_id},
            cabeceras={"Idempotency-Key": idempotency_key},
        )
