from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException

from app.api.v1.schemas import ConteoSalida, ErrorSalida, MetricasSalida
from app.application import casos_uso
from app.dependencies import Uow
from app.seguridad import LlamanteDep

router = APIRouter(prefix="/v1", tags=["analitica"])
ERRORES = {403: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.get("/metricas", response_model=MetricasSalida, responses=ERRORES)
async def metricas(
    uow: Uow,
    llamante: LlamanteDep,
    desde: date,
    hasta: date,
):
    """Conteos agregados de eventos de ciclo de vida de póliza (HU-68/69).

    Solo operador: estas métricas son de back-office, nunca del propio cliente.
    """
    if llamante.rol != "operador":
        raise HTTPException(status_code=403, detail="Rol no autorizado")
    if hasta < desde:
        raise HTTPException(status_code=422, detail="'hasta' no puede ser anterior a 'desde'")
    conteos = await casos_uso.listar_metricas(uow, desde, hasta)
    return MetricasSalida(conteos=[ConteoSalida.desde(c) for c in conteos])
