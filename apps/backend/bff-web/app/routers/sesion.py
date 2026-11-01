from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..clients.base import RechazoDelNucleo
from ..clients.ms_identidad import ClienteMsIdentidad
from ..dependencies import ROLES, issue_pair, obtener_cliente_identidad, refresh_session, require_roles

router = APIRouter(prefix="/sesion", tags=["sesion"])

ClienteIdentidad = Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)]


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
async def ingreso(body: Ingreso, cliente_identidad: ClienteIdentidad) -> dict:
    rol = body.rol if body.rol is not None else _rol_asignado(body.correo)
    if rol not in ROLES:
        raise HTTPException(status_code=400, detail="Rol no permitido")

    # ms-identidad confirma identidad; el rol es un concepto de aplicacion
    # que ms-identidad no conoce, asi que sigue viniendo de _rol_asignado/
    # body.rol como antes. Si ms-identidad rechaza (correo inexistente o
    # contrasena incorrecta), responde 401 igual que el stub anterior.
    try:
        await cliente_identidad.autenticar(email=body.correo, password=body.contrasena)
    except RechazoDelNucleo as exc:
        raise HTTPException(status_code=401, detail="Credenciales invalidas") from exc

    return issue_pair(body.correo, rol)


@router.post("/refresh")
def refresh(body: Refresh) -> dict:
    return refresh_session(body.refreshToken)


@router.post("/salida", dependencies=[Depends(require_roles(*ROLES))])
def salida() -> dict:
    return {"estado": "aceptada"}
