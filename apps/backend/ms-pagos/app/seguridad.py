import os
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"
ROLES = frozenset({"cliente", "asesor", "operador"})
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Llamante:
    uid: UUID
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
    return Llamante(uid=UUID(str(payload["uid"])), rol=str(payload["rol"]), sub=str(payload.get("sub", "")))


LlamanteDep = Annotated[Llamante, Depends(exigir_llamante)]
