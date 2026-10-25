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

    async def obtener_producto(self, producto: str) -> dict[str, Any]:
        """Catálogo de un producto (HU-1/HU-2, SOLV-94/SOLV-95): coberturas y
        rangos válidos de datos de riesgo. Usado por GET /cliente/catalogo/
        {ramo} y /asesor/catalogo/{ramo} para bloquear "Continuar" en el
        frontend antes de cotizar, sin esperar al 422 de ms-cotizacion."""
        return await self._pedir("GET", f"/v1/productos/{producto}")

    async def reconsultar_por_oferta(self, oferta_id: UUID) -> dict[str, Any]:
        """Resuelve el producto real de una oferta ya emitida -- ms-polizas
        solo guarda oferta_id, no cotizacion_id (ver billetera()/detalle() en
        routers/cliente.py)."""
        return await self._pedir("GET", f"/v1/cotizaciones/por-oferta/{oferta_id}")

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
