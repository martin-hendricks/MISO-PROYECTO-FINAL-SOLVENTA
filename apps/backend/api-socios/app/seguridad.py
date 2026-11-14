from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import APIKeyHeader

NOMBRE_CABECERA = "X-Socio-Api-Key"
_api_key_header = APIKeyHeader(name=NOMBRE_CABECERA, auto_error=False)


@dataclass(frozen=True)
class Socio:
    socio_id: str


def _mapa_api_keys(request: Request) -> dict[str, str]:
    """api_key -> socio_id, construido desde `Settings.socios_api_keys`."""
    return request.app.state.config.mapa_socios_api_keys()


def exigir_api_key_socio(
    request: Request,
    api_key: Annotated[str | None, Depends(_api_key_header)],
) -> Socio:
    """Cada socio externo (empresa aliada que integra cotización embebida) se
    identifica con una API key estática propia, enviada en `X-Socio-Api-Key`.
    No es un JWT de sesión: no hay un flujo de login para un socio externo,
    es autenticación servicio-a-servicio con una credencial fija por socio."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key de socio requerida")
    socio_id = _mapa_api_keys(request).get(api_key)
    if socio_id is None:
        raise HTTPException(status_code=401, detail="API key de socio invalida")
    return Socio(socio_id=socio_id)


SocioDep = Annotated[Socio, Depends(exigir_api_key_socio)]
