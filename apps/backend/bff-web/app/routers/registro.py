from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..dependencies import issue_pair

router = APIRouter(prefix="/registro", tags=["registro"])

# Stub hasta que ms-consentimiento versione la politica de tratamiento de datos.
POLITICA_VERSION = "2026-10"


class Alta(BaseModel):
    nombre: str = Field(min_length=1)
    apellidos: str = Field(min_length=1)
    documento: str = Field(min_length=1)
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)
    habeasData: bool


@router.post("")
def alta(body: Alta) -> dict:
    # El alta solo existe con habeas data: el consentimiento no se otorga despues desde Perfil.
    if not body.habeasData:
        raise HTTPException(status_code=422, detail="Consentimiento de datos requerido")
    # Stub hasta que ms-identidad cree la cuenta: la contrasena no se guarda ni se devuelve.
    return {
        **issue_pair(body.correo, "cliente"),
        "cliente": body.model_dump(include={"nombre", "apellidos", "documento", "correo"}),
        "consentimiento": {
            "habeasData": True,
            "otorgadoEn": datetime.now(timezone.utc).isoformat(),
            "version": POLITICA_VERSION,
        },
    }
