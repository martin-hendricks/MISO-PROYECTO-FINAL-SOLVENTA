from __future__ import annotations

from decimal import Decimal
from typing import Any
from uuid import UUID

from .base import ClienteServicio


class ClienteMsCotizacion(ClienteServicio):
    nombre = "ms-cotizacion"

    async def cotizar(
        self,
        idempotency_key: str,
        usuario_id: UUID,
        socio_id: UUID,
        consentimiento_id: UUID,
        producto: str,
        canal: str,
        datos_riesgo: dict[str, Any],
    ) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            "/v1/cotizaciones",
            json={
                "usuario_id": str(usuario_id),
                "socio_id": str(socio_id),
                "consentimiento_id": str(consentimiento_id),
                "producto": producto,
                "canal": canal,
                "datos_riesgo": datos_riesgo,
            },
            cabeceras={"Idempotency-Key": idempotency_key},
        )

    async def reconsultar(self, cotizacion_id: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/cotizaciones/{cotizacion_id}")

    async def aceptar_oferta(
        self,
        cotizacion_id: str,
        idempotency_key: str,
        perfil_id: UUID,
        score: Decimal,
    ) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            f"/v1/cotizaciones/{cotizacion_id}/aceptacion",
            json={"perfil_id": str(perfil_id), "score": str(score)},
            cabeceras={"Idempotency-Key": idempotency_key},
        )
