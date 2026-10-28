from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ..clients.bff_web import autorizacion, es_v1
from ..dependencies import issue_pair, refresh_session, require_customer

router = APIRouter(prefix="/sesion", tags=["sesion"])


class Ingreso(BaseModel):
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)


class Refresh(BaseModel):
    refreshToken: str = Field(min_length=1)


@router.post("/ingreso")
def ingreso(body: Ingreso, request: Request) -> dict:
    if es_v1(request):
        return request.app.state.bff_web.enviar(
            "POST",
            "/v1/sesion/ingreso",
            json={"correo": body.correo, "contrasena": body.contrasena},
        )
    return issue_pair(body.correo)


@router.post("/refresh")
def refresh(body: Refresh, request: Request) -> dict:
    if es_v1(request):
        return request.app.state.bff_web.enviar(
            "POST",
            "/v1/sesion/refresh",
            json={"refreshToken": body.refreshToken},
        )
    return refresh_session(body.refreshToken)


@router.post("/salida", dependencies=[Depends(require_customer())])
def salida(request: Request) -> dict:
    if es_v1(request):
        return request.app.state.bff_web.enviar(
            "POST",
            "/v1/sesion/salida",
            autorizacion=autorizacion(request),
        )
    return {"estado": "aceptada"}
