from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..dependencies import issue_pair, refresh_session, require_customer

router = APIRouter(prefix="/sesion", tags=["sesion"])


class Ingreso(BaseModel):
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)


class Refresh(BaseModel):
    refreshToken: str = Field(min_length=1)


def _sesion_de(usuario: dict, correo_pedido: str) -> dict:
    if not isinstance(usuario, dict):
        raise HTTPException(status_code=502, detail="Respuesta del nucleo incompleta")
    if usuario.get("estado") != "ACTIVO" or not usuario.get("usuario_id"):
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    correo = str(usuario.get("email") or correo_pedido).strip().lower()
    return issue_pair(correo, str(usuario["usuario_id"]))


@router.post("/ingreso")
def ingreso(body: Ingreso, request: Request) -> dict:
    try:
        usuario = request.app.state.nucleo.autenticar(correo=body.correo, contrasena=body.contrasena)
    except HTTPException as exc:
        if exc.status_code == 401:
            raise HTTPException(status_code=401, detail="Credenciales invalidas") from exc
        raise
    return _sesion_de(usuario, body.correo)


@router.post("/refresh")
def refresh(body: Refresh) -> dict:
    return refresh_session(body.refreshToken)


@router.post("/salida", dependencies=[Depends(require_customer)])
def salida() -> dict:
    return {"estado": "aceptada"}
