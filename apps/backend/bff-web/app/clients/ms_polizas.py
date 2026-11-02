from __future__ import annotations

from datetime import date
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

    async def consultar_firma(self, oferta_id: UUID) -> dict[str, Any]:
        """HU-17: constancia persistida de la firma de una oferta."""
        return await self._pedir("GET", f"/v1/polizas/firmas/{oferta_id}")

    async def ofertas_con_poliza(self, oferta_ids: list[UUID]) -> set[str]:
        """HU-163: cuáles de estas ofertas ya tienen póliza emitida."""
        cuerpo = await self._pedir(
            "GET",
            "/v1/polizas/por-ofertas",
            params={"oferta_ids": ",".join(str(oferta_id) for oferta_id in oferta_ids)},
        )
        return {str(oferta_id) for oferta_id in cuerpo["oferta_ids_con_poliza"]}

    async def obtener(self, poliza_id: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/polizas/{poliza_id}")

    async def listar_por_usuario(self, usuario_id: UUID, limite: int) -> list[dict[str, Any]]:
        return await self._pedir(
            "GET", "/v1/polizas", params={"usuario_id": str(usuario_id), "limite": limite}
        )

    async def obtener_por_numero(self, numero: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/polizas/numero/{numero}")

    async def renovar(self, poliza_id: UUID, nueva_fin_vigencia: date) -> dict[str, Any]:
        """HU-59. ms-polizas expone este endpoint por poliza_id (UUID interno),
        no por numero -- operador.py resuelve numero->poliza_id vía
        obtener_por_numero() antes de llamar aquí."""
        return await self._pedir(
            "POST",
            f"/v1/polizas/{poliza_id}/renovacion",
            json={"nueva_fin_vigencia": nueva_fin_vigencia.isoformat()},
        )

    async def modificar_coberturas(self, poliza_id: UUID, coberturas: list[dict[str, Any]]) -> dict[str, Any]:
        """HU-60. Mismo comentario que renovar() sobre poliza_id vs numero."""
        return await self._pedir(
            "POST",
            f"/v1/polizas/{poliza_id}/coberturas",
            json={"coberturas": coberturas},
        )

    async def cancelar(self, poliza_id: UUID, motivo: str, operador: str) -> dict[str, Any]:
        """HU-61. Mismo comentario que renovar() sobre poliza_id vs numero.
        `operador` es la identidad (sub del JWT) que ms-polizas audita como
        cancelada_por."""
        return await self._pedir(
            "POST",
            f"/v1/polizas/{poliza_id}/cancelacion",
            json={"motivo": motivo, "operador": operador},
        )
