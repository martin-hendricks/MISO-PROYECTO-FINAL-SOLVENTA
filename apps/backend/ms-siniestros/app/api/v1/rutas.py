from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.application import casos_uso
from app.dependencies import obtener_adaptador_desembolso, obtener_uow
from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import FabricaUnidadDeTrabajo

from .schemas import (
    CambiarEstadoEntrada,
    ErrorSalida,
    EventoParametricoEntrada,
    ResultadoIngestaSalida,
    SiniestroSalida,
)

router = APIRouter(prefix="/v1", tags=["siniestros"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Desembolso = Annotated[AdaptadorDesembolso, Depends(obtener_adaptador_desembolso)]
ERRORES = {404: {"model": ErrorSalida}, 409: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.post(
    "/eventos-parametricos",
    response_model=ResultadoIngestaSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def ingerir_evento_parametrico(
    entrada: EventoParametricoEntrada, response: Response, uow: Uow, adaptador_desembolso: Desembolso
):
    """HU-32 + HU-33 + HU-34: ingiere el evento paramétrico simulado, encadena la
    evaluación del umbral y, si corresponde, dispara el pago paramétrico stub."""
    resultado = await casos_uso.recibir_evento_parametrico(
        uow,
        adaptador_desembolso,
        entrada.evento_id,
        entrada.valor,
        entrada.umbral,
        entrada.poliza_vigente,
        entrada.monto_pago,
    )
    if not resultado.procesado:
        response.status_code = status.HTTP_200_OK
    return ResultadoIngestaSalida.desde(resultado)


@router.get("/siniestros", response_model=list[SiniestroSalida])
async def listar_siniestros(uow: Uow, limite: Annotated[int, Query(ge=1, le=100)] = 20):
    return [SiniestroSalida.desde(s) for s in await casos_uso.listar_siniestros(uow, limite)]


@router.get("/siniestros/{siniestro_id}", response_model=SiniestroSalida, responses=ERRORES)
async def consultar_siniestro(siniestro_id: UUID, uow: Uow):
    """HU-30: lectura del estado único del siniestro, la misma fuente que leerían todos
    los canales (cola del operador, decisión, pago, lista del cliente)."""
    return SiniestroSalida.desde(await casos_uso.consultar_siniestro(uow, siniestro_id))


@router.post("/siniestros/{siniestro_id}/estado", response_model=SiniestroSalida, responses=ERRORES)
async def cambiar_estado(siniestro_id: UUID, entrada: CambiarEstadoEntrada, uow: Uow):
    """HU-30: aplica una transición de estado explícita. Una transición inválida se
    rechaza con 409 y el siniestro conserva su estado anterior."""
    siniestro = await casos_uso.cambiar_estado_siniestro(uow, siniestro_id, entrada.estado, entrada.origen)
    return SiniestroSalida.desde(siniestro)
