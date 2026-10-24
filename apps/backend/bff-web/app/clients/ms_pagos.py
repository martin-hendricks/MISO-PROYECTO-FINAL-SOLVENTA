from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from .base import ClienteServicio


class ClienteMsPagos(ClienteServicio):
    """Cliente de ms-pagos.

    ms-pagos todavía no existe en develop ni en esta rama: su implementación
    vive en el PR abierto `feature/HU-15-cobro-prima` (origin). Este cliente
    queda listo para cuando ese PR se mergee, pero hoy no se puede probar de
    extremo a extremo (no hay servicio real al que apuntar en este entorno).
    """

    nombre = "ms-pagos"

    async def cobrar_prima(
        self,
        solicitud_id: UUID,
        oferta_id: UUID,
        usuario_id: UUID,
        monto: Decimal,
        token_medio_pago: str,
    ) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            "/v1/pagos/primas",
            json={
                "solicitud_id": str(solicitud_id),
                "oferta_id": str(oferta_id),
                "usuario_id": str(usuario_id),
                "monto": str(monto),
                "token_medio_pago": token_medio_pago,
            },
        )

    async def obtener(self, pago_id: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/pagos/{pago_id}")
