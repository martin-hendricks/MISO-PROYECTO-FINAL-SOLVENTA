from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import ROLES, issue_pair, refresh_session, require_roles

router = APIRouter(prefix="/sesion", tags=["sesion"])


class Ingreso(BaseModel):
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)
    rol: str


class Refresh(BaseModel):
    refreshToken: str = Field(min_length=1)


@router.post("/ingreso")
def ingreso(body: Ingreso) -> dict:
    if body.rol not in ROLES:
        raise HTTPException(status_code=400, detail="Rol no permitido")
    return issue_pair(body.correo, body.rol)


@router.post("/refresh")
def refresh(body: Refresh) -> dict:
    return refresh_session(body.refreshToken)


@router.post("/salida", dependencies=[Depends(require_roles(*ROLES))])
def salida() -> dict:
    return {"estado": "aceptada"}
