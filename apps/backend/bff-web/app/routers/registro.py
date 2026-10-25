from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..clients.base import RechazoDelNucleo
from ..clients.ms_identidad import ClienteMsIdentidad
from ..dependencies import issue_pair, obtener_cliente_identidad

router = APIRouter(prefix="/registro", tags=["registro"])

# Stub hasta que ms-consentimiento versione la politica de tratamiento de datos.
POLITICA_VERSION = "2026-10"

# ms-identidad no conoce tipos de documento distintos todavia (el frontend
# solo captura un numero): se asume cedula de ciudadania, el tipo mas comun
# en el canal web de Solventa. Cuando exista un selector de tipo en la UI,
# este valor fijo debe volverse un campo mas del body de Alta.
TIPO_DOCUMENTO_DEFECTO = "CC"


class Alta(BaseModel):
    nombre: str = Field(min_length=1)
    apellidos: str = Field(min_length=1)
    documento: str = Field(min_length=1)
    correo: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)
    habeasData: bool


ClienteIdentidad = Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)]


@router.post("")
async def alta(body: Alta, cliente_identidad: ClienteIdentidad) -> dict:
    # El alta solo existe con habeas data: el consentimiento no se otorga despues desde Perfil.
    if not body.habeasData:
        raise HTTPException(status_code=422, detail="Consentimiento de datos requerido")

    # ms-identidad persiste documento/correo/contrasena; nombre y apellidos
    # no tienen todavia una tabla de perfil en el nucleo (el schema oficial
    # de ms_identidad.usuario no los contempla), asi que bff-web los sigue
    # devolviendo tal cual los recibio, sin persistirlos en ningun lado.
    try:
        await cliente_identidad.crear_usuario(
            tipo_documento=TIPO_DOCUMENTO_DEFECTO,
            numero_documento=body.documento,
            email=body.correo,
            password=body.contrasena,
        )
    except RechazoDelNucleo as exc:
        raise HTTPException(status_code=409, detail="La cuenta ya existe") from exc

    return {
        **issue_pair(body.correo, "cliente"),
        "cliente": body.model_dump(include={"nombre", "apellidos", "documento", "correo"}),
        "consentimiento": {
            "habeasData": True,
            "otorgadoEn": datetime.now(timezone.utc).isoformat(),
            "version": POLITICA_VERSION,
        },
    }
