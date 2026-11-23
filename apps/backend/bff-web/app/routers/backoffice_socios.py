from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict, Field

from ..clients.ms_identidad import ClienteMsIdentidad
from ..dependencies import obtener_cliente_identidad, require_roles

router = APIRouter(prefix="/backoffice/socios", tags=["backoffice-socios"])

Alcance = Literal[
    "catalogo:leer",
    "originaciones:escribir",
    "cotizaciones:escribir",
    "cotizaciones:leer",
]


class SocioNuevo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: str = Field(min_length=1, max_length=120)
    alcances: list[Alcance] = Field(min_length=1)


def _credencial(credencial: dict[str, Any]) -> dict[str, Any]:
    return {
        "credencialId": credencial["credencial_id"],
        "creadaEn": credencial.get("creada_en"),
        "revocadaEn": credencial.get("revocada_en"),
    }


def _socio(socio: dict[str, Any]) -> dict[str, Any]:
    return {
        "socioId": socio["socio_id"],
        "nombre": socio.get("nombre") or "",
        "alcances": socio.get("alcances") or [],
        "estado": socio.get("estado") or "",
        "creadoEn": socio.get("creado_en"),
        "credenciales": [
            _credencial(credencial) for credencial in socio.get("credenciales") or []
        ],
    }


@router.get("")
async def listar(
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    _: Annotated[dict, Depends(require_roles("operador", "asesor"))],
) -> dict:
    listado = await identidad.listar_socios()
    return {"socios": [_socio(socio) for socio in listado.get("socios") or []]}


@router.post("", status_code=201)
async def crear(
    body: SocioNuevo,
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    _: Annotated[dict, Depends(require_roles("operador", "asesor"))],
) -> dict:
    creado = await identidad.crear_socio(
        nombre=body.nombre, alcances=list(body.alcances)
    )
    return {
        "socioId": creado["socio_id"],
        "nombre": creado.get("nombre") or "",
        "alcances": creado.get("alcances") or [],
        "estado": creado.get("estado") or "",
        "creadoEn": creado.get("creado_en"),
        "credencialId": creado["credencial_id"],
        "apiKey": creado["api_key"],
    }


@router.post("/{socio_id}/credenciales", status_code=201)
async def rotar(
    socio_id: str,
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    _: Annotated[dict, Depends(require_roles("operador", "asesor"))],
) -> dict:
    nueva = await identidad.rotar_credencial_socio(socio_id)
    return {"credencialId": nueva["credencial_id"], "apiKey": nueva["api_key"]}


@router.delete("/{socio_id}/credenciales/{credencial_id}", status_code=204)
async def revocar_credencial(
    socio_id: str,
    credencial_id: str,
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    _: Annotated[dict, Depends(require_roles("operador", "asesor"))],
) -> Response:
    await identidad.revocar_credencial_socio(socio_id, credencial_id)
    return Response(status_code=204)


@router.post("/{socio_id}/revocacion")
async def revocar(
    socio_id: str,
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    _: Annotated[dict, Depends(require_roles("operador", "asesor"))],
) -> dict:
    return _socio(await identidad.revocar_socio(socio_id))
