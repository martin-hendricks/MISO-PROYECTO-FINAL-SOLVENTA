from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.api.v1.schemas import (
    DispositivoSalida,
    ErrorSalida,
    NotificacionSalida,
    RegistrarDispositivoEntrada,
)
from app.application import casos_uso
from app.dependencies import obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import LlamanteDep

router = APIRouter(prefix="/v1/notificaciones", tags=["notificaciones"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
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
