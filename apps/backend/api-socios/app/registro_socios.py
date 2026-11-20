from __future__ import annotations

import time
from collections.abc import Callable
from typing import Protocol
from uuid import UUID

import httpx

from app.clients.base import RecursoNoEncontrado
from app.clients.ms_identidad import ClienteMsIdentidad
from app.clients.token_servicio import token_de_socio
from app.seguridad import Socio

UID_RESOLUCION = "00000000-0000-0000-0000-000000000000"


class RegistroSocios(Protocol):
    async def resolver(self, huella_sha256: str) -> Socio | None: ...


class RegistroSociosIdentidad:
    def __init__(
        self,
        http: httpx.AsyncClient,
        secreto: str,
        ttl_s: float,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        self._http = http
        self._secreto = secreto
        self._ttl_s = ttl_s
        self._reloj = reloj
        self._cache: dict[str, tuple[float, Socio]] = {}

    async def resolver(self, huella_sha256: str) -> Socio | None:
        ahora = self._reloj()
        guardado = self._cache.get(huella_sha256)
        if guardado is not None and guardado[0] > ahora:
            return guardado[1]
        cliente = ClienteMsIdentidad(
            self._http, token=token_de_socio(self._secreto, UID_RESOLUCION)
        )
        try:
            datos = await cliente.resolver_socio(huella_sha256)
        except RecursoNoEncontrado:
            self._cache.pop(huella_sha256, None)
            return None
        socio = Socio(
            socio_id=UUID(str(datos["socio_id"])),
            nombre=str(datos["nombre"]),
            alcances=frozenset(datos["alcances"]),
        )
        self._cache[huella_sha256] = (ahora + self._ttl_s, socio)
        return socio
