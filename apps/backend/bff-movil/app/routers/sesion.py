from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from ..dependencies import issue_pair, refresh_session, require_customer

router = APIRouter(prefix="/sesion", tags=["sesion"])


class Ingreso(BaseModel):
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)


class Refresh(BaseModel):
    refreshToken: str = Field(min_length=1)


def es_v1(request: Request) -> bool:
    return request.url.path.startswith("/v1/")


@router.post("/ingreso")
def ingreso(body: Ingreso, request: Request) -> dict:
    if es_v1(request):
        try:
            request.app.state.nucleo.autenticar(correo=body.correo, contrasena=body.contrasena)
        except HTTPException as exc:
            if exc.status_code == 401:
                raise HTTPException(status_code=401, detail="Credenciales invalidas") from exc
            raise
        return issue_pair(body.correo)
    return issue_pair(body.correo)


@router.post("/refresh")
def refresh(body: Refresh) -> dict:
    return refresh_session(body.refreshToken)


@router.post("/salida", dependencies=[Depends(require_customer)])
def salida() -> dict:
    return {"estado": "aceptada"}
