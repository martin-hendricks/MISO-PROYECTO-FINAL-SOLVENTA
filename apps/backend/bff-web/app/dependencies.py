import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .clients.ms_cotizacion import ClienteMsCotizacion
from .clients.ms_pagos import ClienteMsPagos
from .clients.ms_perfilamiento import ClienteMsPerfilamiento
from .clients.ms_polizas import ClienteMsPolizas
from .clients.ms_siniestros import ClienteMsSiniestros
from .clients.ms_suscripcion import ClienteMsSuscripcion

EXPIRA_EN = 900
ROLES = ("cliente", "asesor", "operador")
ALGORITHM = "HS256"
_bearer = HTTPBearer(auto_error=False)


def secret() -> str:
    value = os.environ.get("SOLVENTA_TOKEN_SECRET", "")
    if not value:
        raise HTTPException(status_code=500, detail="SOLVENTA_TOKEN_SECRET no configurado")
    return value


def _encode(subject: str, rol: str, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "rol": rol,
        "typ": token_type,
        "exp": now + timedelta(seconds=EXPIRA_EN),
    }
    return jwt.encode(payload, secret(), algorithm=ALGORITHM)


def issue_pair(correo: str, rol: str) -> dict:
    return {
        "accessToken": _encode(correo, rol, "access"),
        "refreshToken": _encode(correo, rol, "refresh"),
        "expiraEn": EXPIRA_EN,
    }


def _decode(token: str) -> dict:
    try:
        return jwt.decode(token, secret(), algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token invalido") from exc


def require_roles(*allowed: str):
    async def checker(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    ) -> dict:
        if credentials is None:
            raise HTTPException(status_code=401, detail="Token requerido")
        payload = _decode(credentials.credentials)
        if payload.get("typ") != "access":
            raise HTTPException(status_code=401, detail="Token invalido")
        if allowed and payload.get("rol") not in allowed:
            raise HTTPException(status_code=403, detail="Rol no autorizado")
        return payload

    return checker


def refresh_session(refresh_token: str) -> dict:
    payload = _decode(refresh_token)
    if payload.get("typ") != "refresh" or payload.get("rol") not in ROLES:
        raise HTTPException(status_code=401, detail="Token invalido")
    return issue_pair(payload["sub"], payload["rol"])


def obtener_cliente_cotizacion(request: Request) -> ClienteMsCotizacion:
    return ClienteMsCotizacion(request.app.state.http_ms_cotizacion, getattr(request.state, "correlacion", None))


def obtener_cliente_pagos(request: Request) -> ClienteMsPagos:
    return ClienteMsPagos(request.app.state.http_ms_pagos, getattr(request.state, "correlacion", None))


def obtener_cliente_polizas(request: Request) -> ClienteMsPolizas:
    return ClienteMsPolizas(request.app.state.http_ms_polizas, getattr(request.state, "correlacion", None))


def obtener_cliente_perfilamiento(request: Request) -> ClienteMsPerfilamiento:
    return ClienteMsPerfilamiento(
        request.app.state.http_ms_perfilamiento, getattr(request.state, "correlacion", None)
    )


def obtener_cliente_siniestros(request: Request) -> ClienteMsSiniestros:
    return ClienteMsSiniestros(request.app.state.http_ms_siniestros, getattr(request.state, "correlacion", None))


def obtener_cliente_suscripcion(request: Request) -> ClienteMsSuscripcion:
    return ClienteMsSuscripcion(request.app.state.http_ms_suscripcion, getattr(request.state, "correlacion", None))
