from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..dependencies import issue_pair, refresh_session, require_customer

router = APIRouter(prefix="/sesion", tags=["sesion"])


class Ingreso(BaseModel):
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)


class Refresh(BaseModel):
    refreshToken: str = Field(min_length=1)


@router.post("/ingreso")
def ingreso(body: Ingreso) -> dict:
    return issue_pair(body.correo)


@router.post("/refresh")
def refresh(body: Refresh) -> dict:
    return refresh_session(body.refreshToken)


@router.post("/salida", dependencies=[Depends(require_customer())])
def salida() -> dict:
    return {"estado": "aceptada"}
