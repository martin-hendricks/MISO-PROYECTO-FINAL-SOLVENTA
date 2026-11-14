import os
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"
# "servicio": llamadas internas (ms-polizas consultando GET /v1/pagos/{id}
# para no emitir sin un cobro aprobado, ver token_servicio.py del lado
# emisor). El resto son roles de usuario humano -- bff-web llama aquí con el
# JWT real del cliente/asesor/operador.
ROLES = frozenset({"cliente", "asesor", "operador", "servicio"})
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Llamante:
    uid: UUID | None
    rol: str
    sub: str


def _secret() -> str:
    value = os.environ.get("SOLVENTA_TOKEN_SECRET", "")
    if not value:
        raise HTTPException(status_code=500, detail="SOLVENTA_TOKEN_SECRET no configurado")
    return value


def exigir_llamante(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Llamante:
    if credentials is None:
        raise HTTPException(status_code=401, detail="Token requerido")
    try:
        payload = jwt.decode(credentials.credentials, _secret(), algorithms=[ALGORITHM])
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="Token invalido") from exc
    if payload.get("typ") != "access" or payload.get("rol") not in ROLES or not payload.get("uid"):
        raise HTTPException(status_code=401, detail="Token invalido")
    rol = str(payload["rol"])
    # Un token de servicio lleva el nombre del emisor en `uid` (ver
    # token_servicio.py), no el UUID de un usuario humano.
    uid = None if rol == "servicio" else UUID(str(payload["uid"]))
    return Llamante(uid=uid, rol=rol, sub=str(payload.get("sub", "")))


LlamanteDep = Annotated[Llamante, Depends(exigir_llamante)]
