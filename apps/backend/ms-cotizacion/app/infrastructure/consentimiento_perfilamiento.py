from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

import httpx

from app.domain.errores import DependenciaNoDisponible


class ConsentimientoPerfilamientoHTTP:
    def __init__(self, http: httpx.AsyncClient, productos: Iterable[str]) -> None:
        self._http = http
        self._productos = frozenset(productos)

    def requiere(self, producto: str) -> bool:
        return producto in self._productos

    async def vigente(self, usuario_id: UUID) -> bool:
        try:
            respuesta = await self._http.get(f"/v1/consentimientos/{usuario_id}")
        except httpx.HTTPError as exc:
            raise DependenciaNoDisponible("ms-perfilamiento") from exc
        if respuesta.status_code == 200:
            return True
        if respuesta.status_code in (403, 404):
            return False
        raise DependenciaNoDisponible("ms-perfilamiento")
