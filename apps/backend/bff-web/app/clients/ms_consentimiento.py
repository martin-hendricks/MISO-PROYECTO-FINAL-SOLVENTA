from __future__ import annotations

from typing import Any

from .base import ClienteServicio


class ClienteMsConsentimiento(ClienteServicio):
    """Cliente de ms-consentimiento (habeas data, HU-141/SOLV-...): servicio
    DISTINTO de ms-perfilamiento (consentimiento de perfilamiento
    hipotecario, ver ClienteMsPerfilamiento). Se usa hoy únicamente al dar de
    alta un cliente nuevo desde el back-office (routers/asesor.py)."""

    nombre = "ms-consentimiento"

    async def otorgar_consentimiento(self, cliente_id: str) -> dict[str, Any]:
        """POST /v1/consentimientos. Idempotente del lado del servicio: si ya
        hay uno vigente para ese cliente_id, responde 200 con el existente
        en vez de duplicarlo."""
        return await self._pedir(
            "POST",
            "/v1/consentimientos",
            json={"cliente_id": cliente_id},
        )
