from __future__ import annotations

from typing import Any

from .base import ClienteServicio


class ClienteMsEjemplo(ClienteServicio):
    nombre = "ms-ejemplo"

    async def listar(self, limite: int) -> list[dict[str, Any]]:
        return await self._pedir("GET", "/v1/ejemplos", params={"limite": limite})

    async def indicadores(self, timeout: float | None = None) -> dict[str, Any]:
        return await self._pedir("GET", "/v1/ejemplos/indicadores", timeout=timeout)

    async def obtener(self, ejemplo_id: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/ejemplos/{ejemplo_id}")

    async def registrar(self, referencia: str, monto: str, idempotency_key: str) -> tuple[dict[str, Any], bool]:
        respuesta = await self._enviar(
            "POST",
            "/v1/ejemplos",
            json={"referencia": referencia, "monto": monto},
            cabeceras={"Idempotency-Key": idempotency_key},
        )
        return respuesta.json(), respuesta.status_code == 201

    async def aprobar(self, ejemplo_id: str) -> dict[str, Any]:
        return await self._pedir("POST", f"/v1/ejemplos/{ejemplo_id}/aprobacion")
