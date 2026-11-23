from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.v1.schemas import (
    AudienciaSalida,
    AudienciaUsuarioSalida,
    DifusionCreadaSalida,
    DifusionEntrada,
    DifusionSalida,
    DispositivoSalida,
    ErrorSalida,
    HistorialSalida,
    NotificacionSalida,
    RegistrarDispositivoEntrada,
    TokenEntrada,
)
from app.domain.errores import ReglaDeNegocioViolada
from app.application import casos_uso
from app.dependencies import obtener_push, obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.push import EnviadorPush
from app.seguridad import LlamanteDep

router = APIRouter(prefix="/v1/notificaciones", tags=["notificaciones"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Push = Annotated[EnviadorPush, Depends(obtener_push)]
ERRORES = {404: {"model": ErrorSalida}, 409: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.post(
    "/dispositivos",
    response_model=DispositivoSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def registrar_dispositivo(
    entrada: RegistrarDispositivoEntrada,
    response: Response,
    uow: Uow,
    llamante: LlamanteDep,
):
    """Upsert por (usuario_id, token): 201 la primera vez, 200 si ya existía."""
    resultado = await casos_uso.registrar_dispositivo(
        uow, llamante.uid, entrada.plataforma, entrada.token
    )
    if not resultado.creado:
        response.status_code = status.HTTP_200_OK
    return DispositivoSalida.desde(resultado.dispositivo)


@router.delete(
    "/dispositivos/{dispositivo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERRORES,
)
async def desactivar_dispositivo(dispositivo_id: UUID, uow: Uow, llamante: LlamanteDep):
    await casos_uso.desactivar_dispositivo(uow, llamante.uid, dispositivo_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


def _rol(llamante, *roles: str) -> None:
    if llamante.rol not in roles:
        raise HTTPException(status_code=403, detail="Rol no autorizado")


@router.delete("/dispositivos", status_code=status.HTTP_204_NO_CONTENT, responses=ERRORES)
async def desactivar_por_token(entrada: TokenEntrada, uow: Uow, llamante: LlamanteDep):
    await casos_uso.desactivar_dispositivo_por_token(uow, llamante.uid, entrada.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/audiencia", response_model=AudienciaSalida, responses=ERRORES)
async def audiencia(
    uow: Uow,
    llamante: LlamanteDep,
    usuario_ids: Annotated[list[UUID] | None, Query(alias="usuarioIds")] = None,
):
    ids = usuario_ids or []
    if llamante.rol == "asesor" and not ids:
        raise HTTPException(status_code=403, detail="Rol no autorizado")
    if llamante.rol not in ("operador", "asesor"):
        raise HTTPException(status_code=403, detail="Rol no autorizado")
    if len(ids) > 50:
        raise ReglaDeNegocioViolada("audiencia_larga", "La consulta admite como máximo 50 usuarios")
    conteos = await casos_uso.listar_audiencia(uow, ids or None)
    return AudienciaSalida(
        usuarios=[
            AudienciaUsuarioSalida(usuarioId=usuario_id, dispositivosActivos=cantidad)
            for usuario_id, cantidad in conteos
        ]
    )


@router.post(
    "/difusiones",
    response_model=DifusionCreadaSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def crear_difusion(entrada: DifusionEntrada, uow: Uow, push: Push, llamante: LlamanteDep):
    _rol(llamante, "operador")
    resultado = await casos_uso.difundir(
        uow,
        push,
        llamante.uid,
        entrada.titulo,
        entrada.cuerpo,
        entrada.audiencia.tipo,
        entrada.audiencia.usuarioIds,
        entrada.poliza,
    )
    return DifusionCreadaSalida(
        difusionId=resultado.difusion_id,
        enviadas=resultado.enviadas,
        fallidas=resultado.fallidas,
        sinDispositivo=resultado.sin_dispositivo,
    )


@router.get("/difusiones", response_model=HistorialSalida, responses=ERRORES)
async def historial_difusiones(
    uow: Uow,
    llamante: LlamanteDep,
    limite: Annotated[int, Query(ge=1, le=50)] = 20,
    antes_de: Annotated[datetime | None, Query(alias="antesDe")] = None,
):
    _rol(llamante, "operador")
    items = await casos_uso.listar_difusiones(uow, limite, antes_de)
    return HistorialSalida(items=[DifusionSalida.desde(item) for item in items])


@router.get("", response_model=list[NotificacionSalida], responses=ERRORES)
async def listar(
    uow: Uow,
    llamante: LlamanteDep,
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
    antes_de: datetime | None = None,
):
    """Solo las notificaciones del llamante, más recientes primero, con paginación por cursor."""
    return [
        NotificacionSalida.desde(n)
        for n in await casos_uso.listar_notificaciones(uow, llamante.uid, limite, antes_de)
    ]


@router.post(
    "/{notificacion_id}/leida", response_model=NotificacionSalida, responses=ERRORES
)
async def marcar_leida(notificacion_id: UUID, uow: Uow, llamante: LlamanteDep):
    return NotificacionSalida.desde(
        await casos_uso.marcar_leida(uow, llamante.uid, notificacion_id)
    )


@router.get("/{notificacion_id}", response_model=NotificacionSalida, responses=ERRORES)
async def consultar(notificacion_id: UUID, uow: Uow, llamante: LlamanteDep):
    return NotificacionSalida.desde(
        await casos_uso.consultar_notificacion(uow, llamante.uid, notificacion_id)
    )
