from __future__ import annotations

from typing import Any

import httpx


class ServicioNoDisponible(Exception):
    def __init__(self, servicio: str) -> None:
        super().__init__(servicio)
        self.servicio = servicio


class RecursoNoEncontrado(Exception):
    pass


class RechazoDelNucleo(Exception):
    def __init__(self, status: int, codigo: str, mensaje: str) -> None:
        super().__init__(mensaje)
        self.status = status
        self.codigo = codigo
        self.mensaje = mensaje


class ClienteServicio:
    nombre = "servicio"

    def __init__(self, http: httpx.AsyncClient, correlacion: str | None = None) -> None:
        self._http = http
        self._cabeceras = {"X-Correlation-Id": correlacion} if correlacion else {}

    async def _pedir(self, metodo: str, ruta: str, **kwargs: Any) -> Any:
        return (await self._enviar(metodo, ruta, **kwargs)).json()

    async def _enviar(
        self,
        metodo: str,
        ruta: str,
        *,
        json: Any = None,
        params: dict | None = None,
        cabeceras: dict | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        try:
            respuesta = await self._http.request(
                metodo,
                ruta,
                json=json,
                params=params,
                headers={**self._cabeceras, **(cabeceras or {})},
                timeout=timeout if timeout is not None else httpx.USE_CLIENT_DEFAULT,
            )
        except httpx.HTTPError as exc:
            raise ServicioNoDisponible(self.nombre) from exc

        if respuesta.status_code == 404:
            raise RecursoNoEncontrado(ruta)
        if respuesta.status_code in (409, 422):
            cuerpo = _json_o_vacio(respuesta)
            raise RechazoDelNucleo(
                respuesta.status_code,
                str(cuerpo.get("codigo", "rechazado")),
                str(cuerpo.get("mensaje", "Operación rechazada")),
            )
        if respuesta.status_code >= 400:
            raise ServicioNoDisponible(self.nombre)
        return respuesta


def _json_o_vacio(respuesta: httpx.Response) -> dict:
    try:
        cuerpo = respuesta.json()
    except ValueError:
        return {}
    return cuerpo if isinstance(cuerpo, dict) else {}
