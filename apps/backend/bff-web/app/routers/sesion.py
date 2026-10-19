from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import ROLES, issue_pair, refresh_session, require_roles

router = APIRouter(prefix="/sesion", tags=["sesion"])

# Stub hasta que ms-identidad valide credenciales: esta contraseña siempre falla.
CONTRASENA_RECHAZADA = "incorrecta"


class Ingreso(BaseModel):
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)
    rol: str | None = None


class Refresh(BaseModel):
    refreshToken: str = Field(min_length=1)


def _rol_asignado(correo: str) -> str:
    # Stub hasta que ms-identidad asigne el rol de la cuenta corporativa.
    return "operador" if correo.lower().startswith("operador") else "asesor"


@router.post("/ingreso")
def ingreso(body: Ingreso) -> dict:
    rol = body.rol if body.rol is not None else _rol_asignado(body.correo)
    if rol not in ROLES:
        raise HTTPException(status_code=400, detail="Rol no permitido")
    if body.contrasena == CONTRASENA_RECHAZADA:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    return issue_pair(body.correo, rol)


@router.post("/refresh")
def refresh(body: Refresh) -> dict:
    return refresh_session(body.refreshToken)


@router.post("/salida", dependencies=[Depends(require_roles(*ROLES))])
def salida() -> dict:
    return {"estado": "aceptada"}
