from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from ..clients.base import RechazoDelNucleo, RecursoNoEncontrado, ServicioNoDisponible
from ..clients.ms_identidad import ClienteMsIdentidad
from ..clients.notificaciones import ClienteNotificaciones
from ..dependencies import (
    obtener_cliente_identidad,
    obtener_cliente_notificaciones,
    require_roles,
)

router = APIRouter(prefix="/operador/clientes", tags=["operador-clientes"])


class ClienteNuevo(BaseModel):
    tipoDocumento: str = Field(min_length=1)
    documento: str = Field(min_length=1)
    email: str = Field(min_length=1)
    password: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    apellidos: str = Field(min_length=1)


class ClienteEdicion(BaseModel):
    nombre: str = Field(min_length=1)
    apellidos: str = Field(min_length=1)
    email: str = Field(min_length=1)


class EstadoCliente(BaseModel):
    estado: str = Field(pattern="^(ACTIVO|INACTIVO)$")


def _cliente(usuario: dict[str, Any], dispositivos: int | None) -> dict[str, Any]:
    return {
        "usuarioId": usuario["usuario_id"],
        "nombre": usuario.get("nombre") or "",
        "apellidos": usuario.get("apellidos") or "",
        "email": usuario.get("email") or "",
        "documento": usuario.get("numero_documento") or "",
        "estado": usuario.get("estado") or "",
        "dispositivosActivos": dispositivos,
    }


@router.get("")
async def listar(
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    notificaciones: Annotated[ClienteNotificaciones, Depends(obtener_cliente_notificaciones)],
    _: Annotated[dict, Depends(require_roles("operador", "asesor"))],
    q: Annotated[str | None, Query()] = None,
    estado: Annotated[str | None, Query()] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
) -> dict:
    """Cartera real de clientes. La columna Push sale de la audiencia de esa
    página; si notificaciones no responde, la lista igual sale y el conteo
    queda null."""
    listado = await identidad.listar_clientes(q=q, estado=estado, pagina=pagina)
    usuarios = listado.get("usuarios") or []
    activos: dict[str, int] | None
    if not usuarios:
        activos = {}
    else:
        try:
            audiencia = await notificaciones.audiencia([usuario["usuario_id"] for usuario in usuarios])
            activos = {item["usuarioId"]: int(item["dispositivosActivos"]) for item in audiencia.get("usuarios") or []}
        except (ServicioNoDisponible, RechazoDelNucleo, RecursoNoEncontrado):
            activos = None
    return {
        "clientes": [
            _cliente(usuario, None if activos is None else activos.get(usuario["usuario_id"], 0))
            for usuario in usuarios
        ],
        "pagina": listado.get("pagina", pagina),
        "hayMas": bool(listado.get("hay_mas")),
    }


@router.post("", status_code=201)
async def crear(
    body: ClienteNuevo,
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    _: Annotated[dict, Depends(require_roles("operador"))],
) -> dict:
    creado = await identidad.crear_usuario(
        tipo_documento=body.tipoDocumento,
        numero_documento=body.documento,
        email=body.email,
        password=body.password,
        nombre=body.nombre,
        apellidos=body.apellidos,
    )
    return _cliente(creado, None)


@router.patch("/{usuario_id}")
async def editar(
    usuario_id: str,
    body: ClienteEdicion,
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    _: Annotated[dict, Depends(require_roles("operador"))],
) -> dict:
    guardado = await identidad.editar_cliente(
        usuario_id, nombre=body.nombre, apellidos=body.apellidos, email=body.email
    )
    return _cliente(guardado, None)


@router.post("/{usuario_id}/estado")
async def cambiar_estado(
    usuario_id: str,
    body: EstadoCliente,
    identidad: Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)],
    _: Annotated[dict, Depends(require_roles("operador"))],
) -> dict:
    guardado = await identidad.cambiar_estado(usuario_id, estado=body.estado)
    return _cliente(guardado, None)
