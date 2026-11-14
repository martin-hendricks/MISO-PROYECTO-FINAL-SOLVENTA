import os
from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ALGORITHM = "HS256"
ROLES = frozenset({"cliente", "asesor", "operador", "socio"})
ROLES_BUSQUEDA_POR_DOCUMENTO = frozenset({"asesor", "operador", "socio"})
ROLES_BACKOFFICE = frozenset({"asesor", "operador"})
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


def alcance(llamante: Llamante, usuario_id: UUID | None) -> UUID | None:
    """El cliente solo ve lo suyo. Un rol de back-office debe declararse; omitir el filtro no abre datos a un anónimo."""
    if llamante.rol == "cliente":
        if usuario_id is not None and usuario_id != llamante.uid:
            raise HTTPException(status_code=404, detail="No existe")
        return llamante.uid
    if llamante.rol not in ("asesor", "operador"):
        raise HTTPException(status_code=403, detail="Rol no autorizado")
    return usuario_id


LlamanteDep = Annotated[Llamante, Depends(exigir_llamante)]


def exigir_backoffice(llamante: LlamanteDep) -> Llamante:
    """Operador o asesor. El cliente no lista cuentas ajenas."""
    if llamante.rol not in ("operador", "asesor"):
        raise HTTPException(status_code=403, detail="Rol no autorizado")
    return llamante


def exigir_operador(llamante: LlamanteDep) -> Llamante:
    if llamante.rol != "operador":
        raise HTTPException(status_code=403, detail="Rol no autorizado")
    return llamante


def exigir_busqueda_por_documento(llamante: Llamante) -> None:
    """Saber a quién pertenece una cédula es un dato personal: no lo resuelve un cliente."""
    if llamante.rol not in ROLES_BUSQUEDA_POR_DOCUMENTO:
        raise HTTPException(status_code=403, detail="Rol no autorizado")


def exigir_rol_backoffice(llamante: Llamante) -> None:
    """Listar/consultar/desactivar clientes (HU-141) es una operación del
    back-office: ni el propio cliente ni un socio externo deben poder
    listar la cartera completa de clientes de la plataforma."""
    if llamante.rol not in ROLES_BACKOFFICE:
        raise HTTPException(status_code=403, detail="Rol no autorizado")
