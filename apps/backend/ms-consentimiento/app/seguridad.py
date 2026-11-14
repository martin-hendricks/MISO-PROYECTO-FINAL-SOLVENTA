import os
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"
# "servicio": llamadas internas (ms-identidad resolviendo el campo
# consentimiento del listado de clientes, ver token_servicio.py del lado
# emisor). El resto son roles de usuario humano -- bff-web llama aquí con
# el JWT real del asesor/operador que da de alta un cliente.
ROLES = frozenset({"cliente", "asesor", "operador", "servicio"})
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Llamante:
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
    if payload.get("typ") != "access" or payload.get("rol") not in ROLES:
        raise HTTPException(status_code=401, detail="Token invalido")
    return Llamante(rol=str(payload["rol"]), sub=str(payload.get("sub", "")))


LlamanteDep = Annotated[Llamante, Depends(exigir_llamante)]
