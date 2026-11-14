from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from ..clients.base import RechazoDelNucleo
from ..clients.ms_identidad import ClienteMsIdentidad
from ..dependencies import (
    ROLES,
    issue_pair,
    obtener_cliente_identidad,
    refresh_session,
    require_roles,
    revocar_token,
)

router = APIRouter(prefix="/sesion", tags=["sesion"])

ClienteIdentidad = Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)]
_bearer = HTTPBearer(auto_error=False)


class Ingreso(BaseModel):
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)
    rol: str | None = None


class Refresh(BaseModel):
    refreshToken: str = Field(min_length=1)


class Salida(BaseModel):
    """refreshToken es opcional por compatibilidad, pero es el que importa
    revocar de verdad: es el que permite reautenticarse indefinidamente
    mientras no expire (hasta 15 minutos) si no se invalida en el logout."""

    refreshToken: str | None = None


def _rol_de_identidad(usuario: dict) -> str:
    rol = str(usuario.get("rol") or "cliente")
    return rol if rol in ROLES else "cliente"


@router.post("/ingreso")
async def ingreso(body: Ingreso, cliente_identidad: ClienteIdentidad) -> dict:
    if body.rol is not None and body.rol not in ROLES:
        raise HTTPException(status_code=400, detail="Rol no permitido")
    try:
        usuario = await cliente_identidad.autenticar(email=body.correo, password=body.contrasena)
    except RechazoDelNucleo as exc:
        if exc.status == 403:
            raise HTTPException(status_code=403, detail=exc.mensaje) from exc
        raise HTTPException(status_code=401, detail="Credenciales invalidas") from exc
    if usuario.get("estado") != "ACTIVO" or not usuario.get("usuario_id") or not usuario.get("email"):
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    rol = _rol_de_identidad(usuario)
    if body.rol is not None and body.rol != rol:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    return issue_pair(usuario["email"], rol, str(usuario["usuario_id"]))


@router.post("/refresh")
def refresh(body: Refresh) -> dict:
    return refresh_session(body.refreshToken)


@router.post("/salida")
def salida(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    _payload: Annotated[dict, Depends(require_roles(*ROLES))],
    body: Salida | None = None,
) -> dict:
    # require_roles ya validó el access token (y que no esté revocado); acá
    # lo revocamos de verdad -- antes este endpoint no invalidaba nada del
    # lado servidor. El refresh token es el hueco mas importante: si el
    # cliente lo manda en el body, se revoca tambien, para que no se pueda
    # seguir reautenticando con el despues de un logout.
    if credentials is not None:
        revocar_token(credentials.credentials)
    if body is not None and body.refreshToken:
        revocar_token(body.refreshToken)
    return {"estado": "aceptada"}
