from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

import httpx

from app.domain.errores import DependenciaNoDisponible

from .token_servicio import token_de_servicio


class ConsentimientoPerfilamientoHTTP:
    """ms-perfilamiento ya exige autenticación (rechaza llamadas sin token):
    se genera un token de servicio nuevo en cada llamada (dura 5 minutos,
    no se puede reusar de un arranque a otro de este proceso)."""

    def __init__(self, http: httpx.AsyncClient, productos: Iterable[str], secreto: str) -> None:
        self._http = http
        self._productos = frozenset(productos)
        self._secreto = secreto

    def requiere(self, producto: str) -> bool:
        return producto in self._productos

    async def vigente(self, usuario_id: UUID) -> bool:
        try:
            respuesta = await self._http.get(
                f"/v1/consentimientos/{usuario_id}",
                headers={"Authorization": f"Bearer {token_de_servicio(self._secreto, 'ms-cotizacion')}"},
            )
        except httpx.HTTPError as exc:
            raise DependenciaNoDisponible("ms-perfilamiento") from exc
        if respuesta.status_code == 200:
            return True
        if respuesta.status_code in (403, 404):
            return False
        raise DependenciaNoDisponible("ms-perfilamiento")
