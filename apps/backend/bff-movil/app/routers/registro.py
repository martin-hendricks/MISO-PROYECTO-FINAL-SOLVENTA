from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/registro", tags=["registro"])


class Alta(BaseModel):
    nombre: str = Field(min_length=1)
    apellidos: str = Field(min_length=1)
    documento: str = Field(min_length=1)
    correo: str = Field(min_length=1)
    pruebaDeVida: str
    habeasData: bool


class Revocacion(BaseModel):
    habeasData: bool


@router.post("")
def alta(body: Alta) -> dict:
    if body.pruebaDeVida not in {"ok", "no"}:
        raise HTTPException(status_code=400, detail="Prueba de vida no permitida")
    return body.model_dump()


@router.post("/consentimiento")
def revocar(body: Revocacion) -> dict:
    if body.habeasData:
        raise HTTPException(status_code=400, detail="La revocacion exige habeasData falso")
    return {"habeasData": False}
