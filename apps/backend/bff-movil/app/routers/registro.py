from decimal import Decimal

from fastapi import APIRouter, HTTPException, Request

from .sesion import _sesion_de
from pydantic import BaseModel, Field

router = APIRouter(prefix="/registro", tags=["registro"])


class Alta(BaseModel):
    nombre: str = Field(min_length=1)
    apellidos: str = Field(min_length=1)
    documento: str = Field(min_length=1)
    correo: str = Field(min_length=1)
    pruebaDeVida: str
    habeasData: bool
    contrasena: str = ""
    tipoDocumento: str = ""
    ingresos_mensuales: Decimal = Field(gt=0)
    gastos_mensuales: Decimal = Field(ge=0)


class Revocacion(BaseModel):
    habeasData: bool


def _publico(body: Alta) -> dict:
    return {
        "nombre": body.nombre,
        "apellidos": body.apellidos,
        "documento": body.documento,
        "correo": body.correo,
        "pruebaDeVida": body.pruebaDeVida,
        "habeasData": body.habeasData,
    }


@router.post("")
def alta(body: Alta, request: Request) -> dict:
    if body.pruebaDeVida not in {"ok", "no"}:
        raise HTTPException(status_code=400, detail="Prueba de vida no permitida")
    tiene_cuenta = bool(body.contrasena) and bool(body.tipoDocumento.strip())
    if "/v1/" in request.url.path and not tiene_cuenta:
        raise HTTPException(status_code=422, detail="Cuenta incompleta")
    if not tiene_cuenta:
        return _publico(body)
    try:
        usuario = request.app.state.nucleo.crear_usuario(
            tipo_documento=body.tipoDocumento.strip(),
            numero_documento=body.documento,
            email=body.correo,
            password=body.contrasena,
            nombre=body.nombre,
            apellidos=body.apellidos,
            ingresos_mensuales=str(body.ingresos_mensuales),
            gastos_mensuales=str(body.gastos_mensuales),
            prueba_de_vida=body.pruebaDeVida,
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            raise HTTPException(status_code=409, detail="La cuenta ya existe") from exc
        raise
    return {**_publico(body), "tipoDocumento": body.tipoDocumento, **_sesion_de(usuario, body.correo)}


@router.post("/consentimiento")
def revocar(body: Revocacion) -> dict:
    if body.habeasData:
        raise HTTPException(status_code=400, detail="La revocacion exige habeasData falso")
    return {"habeasData": False}
