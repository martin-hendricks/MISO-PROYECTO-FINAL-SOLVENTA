from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, Response, status

from app.aggregators.componer import componer
from app.clients.ms_ejemplo import ClienteMsEjemplo
from app.dependencies import obtener_cliente_ejemplo
from app.seguridad import identidad_actual

from .schemas import (
    EjemploVista,
    ErrorVista,
    IndicadoresVista,
    InicioVista,
    RegistrarEjemploEntrada,
)

router = APIRouter(prefix="/v1", dependencies=[Depends(identidad_actual)])
Ejemplos = Annotated[ClienteMsEjemplo, Depends(obtener_cliente_ejemplo)]
ERRORES = {
    401: {"description": "Token ausente, expirado o inválido"},
    403: {"description": "Alcance insuficiente"},
    404: {"model": ErrorVista},
    422: {"model": ErrorVista},
    503: {"model": ErrorVista},
}


@router.get(
    "/inicio",
    response_model=InicioVista,
    response_model_by_alias=True,
    responses=ERRORES,
)
async def inicio(request: Request, ejemplos: Ejemplos):
    config = request.app.state.config
    vista = await componer(
        principal=ejemplos.listar(limite=3),
        opcionales={"indicadores": ejemplos.indicadores(timeout=config.timeout_opcional_s)},
        timeout_opcional=config.timeout_opcional_s,
    )
    indicadores = vista.opcionales["indicadores"]
    return InicioVista(
        ejemplos=[EjemploVista.desde_nucleo(e) for e in vista.principal],
        indicadores=IndicadoresVista(total=indicadores["total"], monto_total=indicadores["monto_total"])
        if indicadores
        else None,
        degradado=vista.degradado,
    )


@router.get(
    "/ejemplos/{ejemplo_id}",
    response_model=EjemploVista,
    response_model_by_alias=True,
    responses=ERRORES,
)
async def consultar(ejemplo_id: str, ejemplos: Ejemplos):
    return EjemploVista.desde_nucleo(await ejemplos.obtener(ejemplo_id))


@router.post(
    "/ejemplos",
    response_model=EjemploVista,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def registrar(
    entrada: RegistrarEjemploEntrada,
    response: Response,
    ejemplos: Ejemplos,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
):
    dato, creado = await ejemplos.registrar(entrada.referencia, str(entrada.monto), idempotency_key)
    if not creado:
        response.status_code = status.HTTP_200_OK
    return EjemploVista.desde_nucleo(dato)


@router.post(
    "/ejemplos/{ejemplo_id}/aprobacion",
    response_model=EjemploVista,
    response_model_by_alias=True,
    responses=ERRORES,
)
async def aprobar(ejemplo_id: str, ejemplos: Ejemplos):
    return EjemploVista.desde_nucleo(await ejemplos.aprobar(ejemplo_id))
