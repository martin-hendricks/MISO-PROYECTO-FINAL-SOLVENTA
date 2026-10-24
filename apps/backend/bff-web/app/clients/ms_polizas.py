from __future__ import annotations

from typing import Any
from uuid import UUID

from .base import ClienteServicio


class ClienteMsPolizas(ClienteServicio):
    """Cliente de ms-polizas.

    ms-polizas todavía no existe en develop ni en esta rama: su implementación
    vive en el PR abierto `feature/HU-16-emitir-poliza` (origin). Este cliente
    queda listo para cuando ese PR se mergee, pero hoy no se puede probar de
    extremo a extremo (no hay servicio real al que apuntar en este entorno).
    """

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
