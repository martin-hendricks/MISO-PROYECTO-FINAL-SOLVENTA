from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from ..dependencies import issue_pair, refresh_session, require_customer, revocar_token

router = APIRouter(prefix="/sesion", tags=["sesion"])
_bearer = HTTPBearer(auto_error=False)


class Ingreso(BaseModel):
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)


class Refresh(BaseModel):
    refreshToken: str = Field(min_length=1)


class Salida(BaseModel):
    """refreshToken es opcional por compatibilidad, pero es el que importa
    revocar de verdad: es el que permite reautenticarse indefinidamente
    mientras no expire (hasta 15 minutos) si no se invalida en el logout."""

    refreshToken: str | None = None


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


@router.post("/salida")
def salida(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    _payload: Annotated[dict, Depends(require_customer)],
    body: Salida | None = None,
) -> dict:
    # require_customer ya validó el access token (y que no esté revocado);
    # acá lo revocamos de verdad -- antes este endpoint no invalidaba nada
    # del lado servidor. El refresh token es el hueco mas importante: si el
    # cliente lo manda en el body, se revoca tambien.
    if credentials is not None:
        revocar_token(credentials.credentials)
    if body is not None and body.refreshToken:
        revocar_token(body.refreshToken)
    return {"estado": "aceptada"}
