from fastapi import APIRouter, HTTPException, Request
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
    if request.url.path.startswith("/v1/") and not tiene_cuenta:
        raise HTTPException(status_code=422, detail="Cuenta incompleta")
    if not tiene_cuenta:
        return _publico(body)
    try:
        request.app.state.nucleo.crear_usuario(
            tipo_documento=body.tipoDocumento.strip(),
            numero_documento=body.documento,
            email=body.correo,
            password=body.contrasena,
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            raise HTTPException(status_code=409, detail="La cuenta ya existe") from exc
        raise
    return {**_publico(body), "tipoDocumento": body.tipoDocumento}


@router.post("/consentimiento")
def revocar(body: Revocacion) -> dict:
    if body.habeasData:
        raise HTTPException(status_code=400, detail="La revocacion exige habeasData falso")
    return {"habeasData": False}
