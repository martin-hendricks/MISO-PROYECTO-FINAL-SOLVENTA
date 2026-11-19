from __future__ import annotations

import hashlib
import hmac
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

from app.config import Alcance, RegistroSocio

NOMBRE_CABECERA = "X-Socio-Api-Key"
_api_key_header = APIKeyHeader(name=NOMBRE_CABECERA, auto_error=False)


@dataclass(frozen=True)
class Socio:
    socio_id: UUID
    nombre: str
    alcances: frozenset[str]


def _buscar_socio(socios: list[RegistroSocio], api_key: str) -> RegistroSocio | None:
    huella = hashlib.sha256(api_key.encode()).hexdigest()
    encontrado = None
    for registro in socios:
        for candidata in registro.api_keys_sha256:
            if hmac.compare_digest(candidata, huella):
                encontrado = registro
    return encontrado


def exigir_api_key_socio(
    request: Request,
    api_key: Annotated[str | None, Depends(_api_key_header)],
) -> Socio:
    if not api_key:
        raise HTTPException(status_code=401, detail="API key de socio requerida")
    registro = _buscar_socio(request.app.state.config.socios, api_key)
    if registro is None:
        raise HTTPException(status_code=401, detail="API key de socio invalida")
    return Socio(socio_id=registro.socio_id, nombre=registro.nombre, alcances=frozenset(registro.alcances))


SocioDep = Annotated[Socio, Depends(exigir_api_key_socio)]


def exigir_alcance(alcance: Alcance) -> Callable[[Socio], Socio]:
    def verificar(socio: SocioDep) -> Socio:
        if alcance not in socio.alcances:
            raise HTTPException(status_code=403, detail="El socio no tiene el alcance requerido")
        return socio

    return verificar
