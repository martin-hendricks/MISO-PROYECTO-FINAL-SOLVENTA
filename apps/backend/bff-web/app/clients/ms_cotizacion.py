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
        asesor_id: UUID | None = None,
        cliente_ref: str | None = None,
    ) -> dict[str, Any]:
        cuerpo = {
            "usuario_id": str(usuario_id),
            "socio_id": str(socio_id),
            "consentimiento_id": str(consentimiento_id),
            "producto": producto,
            "canal": canal,
            "datos_riesgo": datos_riesgo,
        }
        # HU-163: solo la venta asistida los envía; el canal cliente sigue
        # mandando el mismo cuerpo de antes.
        if asesor_id is not None:
            cuerpo["asesor_id"] = str(asesor_id)
        if cliente_ref is not None:
            cuerpo["cliente_ref"] = cliente_ref
        return await self._pedir(
            "POST",
            "/v1/cotizaciones",
            json=cuerpo,
            cabeceras={"Idempotency-Key": idempotency_key},
        )

    async def listar_por_asesor(
        self, asesor_id: UUID, incluir_vencidas: bool, pagina: int, tamano: int
    ) -> dict[str, Any]:
        """HU-163: cotizaciones pendientes (cotizada/aceptada) creadas por un
        asesor, paginadas y ordenadas por creada_en DESC en ms-cotizacion."""
        return await self._pedir(
            "GET",
            "/v1/cotizaciones",
            params={
                "asesor_id": str(asesor_id),
                "estados": "cotizada,aceptada",
                "incluir_vencidas": "true" if incluir_vencidas else "false",
                "pagina": pagina,
                "tamano": tamano,
            },
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
