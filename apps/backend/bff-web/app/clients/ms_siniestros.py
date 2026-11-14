from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from .base import ClienteServicio, RechazoDelNucleo, RecursoNoEncontrado, ServicioNoDisponible

# La carga de evidencia (hasta 5 archivos de 10 MB) tarda más que una llamada normal.
TIMEOUT_CARGA_EVIDENCIA = 30.0


class ClienteMsSiniestros(ClienteServicio):
    nombre = "ms-siniestros"

    async def listar(self, limite: int = 20, **filtros: Any) -> list[dict[str, Any]]:
        params = {"limite": limite} | {
            clave: (str(valor).lower() if isinstance(valor, bool) else str(valor))
            for clave, valor in filtros.items()
            if valor is not None
        }
        return await self._pedir("GET", "/v1/siniestros", params=params)

    async def cambiar_estado(self, siniestro_id: UUID, estado: str, origen: str) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            f"/v1/siniestros/{siniestro_id}/estado",
            json={"estado": estado, "origen": origen},
        )

    async def abiertos_por_poliza(self, poliza_id: UUID) -> int | None:
        """HU-61: dato informativo. Si el servicio no responde, la cancelación sigue."""
        try:
            cuerpo = await self._pedir("GET", "/v1/siniestros/abiertos", params={"poliza_id": str(poliza_id)})
            return int(cuerpo["abiertos"])
        except (ServicioNoDisponible, RecursoNoEncontrado, RechazoDelNucleo, KeyError, TypeError, ValueError):
            return None

    # --- HU-157: siniestro asistido

    async def registrar_aviso(
        self,
        datos: dict[str, Any],
        archivos: list[tuple[str, bytes, str]],
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """POST multipart: `datos` (JSON) + `archivos`. El núcleo guarda la evidencia en S3."""
        respuesta = await self._enviar(
            "POST",
            "/v1/siniestros",
            data={"datos": json.dumps(datos, default=str)},
            files=[("archivos", archivo) for archivo in archivos],
            cabeceras={"Idempotency-Key": idempotency_key} if idempotency_key else None,
            timeout=TIMEOUT_CARGA_EVIDENCIA,
        )
        return respuesta.json()

    async def detalle(self, siniestro_id: UUID, usuario_id: UUID | None = None) -> dict[str, Any]:
        params = {"usuario_id": str(usuario_id)} if usuario_id else None
        return await self._pedir("GET", f"/v1/siniestros/{siniestro_id}/detalle", params=params)

    async def decidir(self, siniestro_id: UUID, resultado: str, motivo: str | None, actor: str) -> dict[str, Any]:
        return await self._pedir(
            "POST",
            f"/v1/siniestros/{siniestro_id}/decision",
            json={"resultado": resultado, "motivo": motivo, "actor": actor},
        )

    async def enrutar_a_perito(self, siniestro_id: UUID, motivo: str | None, actor: str) -> dict[str, Any]:
        return await self._pedir(
            "POST", f"/v1/siniestros/{siniestro_id}/perito", json={"motivo": motivo, "actor": actor}
        )

    async def pagar(self, siniestro_id: UUID, actor: str) -> dict[str, Any]:
        return await self._pedir("POST", f"/v1/siniestros/{siniestro_id}/pago", json={"actor": actor})

    async def pagos_recibidos(self) -> dict[str, Any]:
        return await self._pedir("GET", "/v1/pagos-recibidos")

    async def pago_recibido(self, siniestro_id: UUID) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/pagos-recibidos/{siniestro_id}")
