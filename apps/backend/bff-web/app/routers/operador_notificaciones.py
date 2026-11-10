from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..clients.base import RecursoNoEncontrado
from ..clients.ms_identidad import ClienteMsIdentidad
from ..clients.ms_polizas import ClienteMsPolizas
from ..clients.notificaciones import ClienteNotificaciones
from ..dependencies import (
    obtener_cliente_identidad,
    obtener_cliente_notificaciones,
    obtener_cliente_polizas,
    require_roles,
)

router = APIRouter(
    prefix="/operador/notificaciones",
    tags=["operador-notificaciones"],
    dependencies=[Depends(require_roles("operador"))],
)

_TROZO = 50


class AudienciaEntrada(BaseModel):
    tipo: Literal["todos", "usuarios"]
    usuarioIds: list[str] = Field(default_factory=list)


class DifusionEntrada(BaseModel):
    titulo: str
    cuerpo: str
    audiencia: AudienciaEntrada
    poliza: str | None = None


def _trozos(ids: list[str], tamano: int = _TROZO) -> list[list[str]]:
    return [ids[indice : indice + tamano] for indice in range(0, len(ids), tamano)]


def _audiencia_salida(audiencia: AudienciaEntrada) -> dict[str, Any]:
    if audiencia.tipo == "todos":
        return {"tipo": "todos"}
    return {"tipo": "usuarios", "usuarioIds": audiencia.usuarioIds}


@router.get("/audiencia")
async def audiencia(
    notificaciones: Annotated[ClienteNotificaciones, Depends(obtener_cliente_notificaciones)],
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
) -> dict:
    """Quién tiene dispositivo activo, con el nombre tomado de ms-identidad
    en tandas de 50 (el tope de `ids` del listado de usuarios)."""
    cruda = await notificaciones.audiencia()
    filas = cruda.get("usuarios") or []
    nombres: dict[str, dict[str, Any]] = {}
    ids = [fila["usuarioId"] for fila in filas]
    for trozo in _trozos(ids):
        listado = await identidad.listar_clientes(ids=trozo)
        for usuario in listado.get("usuarios") or []:
            nombres[usuario["usuario_id"]] = usuario
    return {
        "usuarios": [
            {
                "usuarioId": fila["usuarioId"],
                "nombre": (nombres.get(fila["usuarioId"]) or {}).get("nombre") or "",
                "apellidos": (nombres.get(fila["usuarioId"]) or {}).get("apellidos") or "",
                "dispositivosActivos": fila["dispositivosActivos"],
            }
            for fila in filas
        ]
    }


@router.post("/difusiones", status_code=201)
async def difundir(
    body: DifusionEntrada,
    notificaciones: Annotated[ClienteNotificaciones, Depends(obtener_cliente_notificaciones)],
    polizas: Annotated[ClienteMsPolizas, Depends(obtener_cliente_polizas)],
):
    poliza = (body.poliza or "").strip()
    if poliza:
        try:
            await polizas.obtener_por_numero(poliza)
        except RecursoNoEncontrado:
            return JSONResponse(
                status_code=422,
                content={"codigo": "poliza_desconocida", "mensaje": "La póliza no existe"},
            )
    cuerpo: dict[str, Any] = {
        "titulo": body.titulo,
        "cuerpo": body.cuerpo,
        "audiencia": _audiencia_salida(body.audiencia),
    }
    if poliza:
        cuerpo["poliza"] = poliza
    return await notificaciones.difundir(cuerpo)


@router.get("/difusiones")
async def historial(
    notificaciones: Annotated[ClienteNotificaciones, Depends(obtener_cliente_notificaciones)],
    limite: Annotated[int | None, Query(ge=1, le=50)] = None,
    antesDe: Annotated[str | None, Query()] = None,
) -> dict:
    return await notificaciones.historial(limite, antesDe)
