from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/registro", tags=["registro"])


class Alta(BaseModel):
    nombre: str = Field(min_length=1)
    apellidos: str = Field(min_length=1)
    documento: str = Field(min_length=1)
    correo: str = Field(min_length=1)
    habeasData: bool


@router.post("")
def alta(body: Alta) -> dict:
    return body.model_dump()
