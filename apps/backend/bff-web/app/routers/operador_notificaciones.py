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


def _id(fila: dict) -> str:
    valor = fila.get("usuarioId") or fila.get("usuario_id") or ""
    return str(valor).strip().lower()


def _perfil_vacio() -> dict[str, str]:
    return {"nombre": "", "apellidos": "", "email": "", "documento": ""}


def _perfil(usuario: dict) -> dict[str, str]:
    return {
        "nombre": str(usuario.get("nombre") or "").strip(),
        "apellidos": str(usuario.get("apellidos") or "").strip(),
        "email": str(usuario.get("email") or usuario.get("correo") or "").strip(),
        "documento": str(
            usuario.get("numero_documento") or usuario.get("documento") or ""
        ).strip(),
    }


async def _perfil_de(identidad: ClienteMsIdentidad, uid: str, nombres: dict[str, dict]) -> dict[str, str]:
    if not uid:
        return _perfil_vacio()
    usuario = nombres.get(uid)
    if usuario is None:
        try:
            usuario = await identidad.obtener(uid)
        except RecursoNoEncontrado:
            return _perfil_vacio()
        nombres[uid] = usuario
    return _perfil(usuario)


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
    ids = [_id(fila) for fila in filas if _id(fila)]
    for trozo in _trozos(ids):
        listado = await identidad.listar_clientes(ids=trozo)
        for usuario in listado.get("usuarios") or []:
            nombres[_id(usuario)] = usuario
    salida = []
    for fila in filas:
        uid = _id(fila)
        perfil = await _perfil_de(identidad, uid, nombres)
        salida.append(
            {
                "usuarioId": uid,
                "nombre": perfil["nombre"],
                "apellidos": perfil["apellidos"],
                "email": perfil["email"],
                "documento": perfil["documento"],
                "dispositivosActivos": fila.get("dispositivosActivos") or fila.get("dispositivos_activos") or 0,
            }
        )
    return {"usuarios": salida}


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
