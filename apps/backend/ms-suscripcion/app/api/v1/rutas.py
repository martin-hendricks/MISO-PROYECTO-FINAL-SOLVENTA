from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.application import casos_uso
from app.dependencies import obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo

from .schemas import ErrorSalida, EvaluarSuscripcionEntrada, SuscripcionSalida

router = APIRouter(prefix="/v1/suscripciones", tags=["suscripciones"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
ERRORES = {404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}, 503: {"model": ErrorSalida}}


@router.post("", response_model=SuscripcionSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def evaluar(entrada: EvaluarSuscripcionEntrada, response: Response, uow: Uow):
    """Idempotente por solicitud_id: un reintento responde 200 con la decisión ya persistida."""
    resultado = await casos_uso.evaluar_suscripcion(uow, entrada.solicitud_id, entrada.perfil_id, entrada.score)
    if not resultado.creada:
        response.status_code = status.HTTP_200_OK
    return SuscripcionSalida.desde(resultado.suscripcion)


@router.get("/{solicitud_id}", response_model=SuscripcionSalida, responses=ERRORES)
async def consultar(solicitud_id: UUID, uow: Uow):
    return SuscripcionSalida.desde(await casos_uso.consultar_suscripcion(uow, solicitud_id))
