from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response, status

from app.application import casos_uso
from app.dependencies import obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo

from .schemas import EjemploSalida, ErrorSalida, IndicadoresSalida, RegistrarEjemploEntrada

router = APIRouter(prefix="/v1/ejemplos", tags=["ejemplos"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
ERRORES = {404: {"model": ErrorSalida}, 409: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.post("", response_model=EjemploSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def registrar(
    entrada: RegistrarEjemploEntrada,
    response: Response,
    uow: Uow,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
):
    resultado = await casos_uso.registrar_ejemplo(uow, idempotency_key, entrada.referencia, entrada.monto)
    if not resultado.creado:
        response.status_code = status.HTTP_200_OK
    return EjemploSalida.desde(resultado.ejemplo)


@router.get("", response_model=list[EjemploSalida])
async def listar(uow: Uow, limite: Annotated[int, Query(ge=1, le=100)] = 20):
    return [EjemploSalida.desde(e) for e in await casos_uso.listar_ejemplos(uow, limite)]


@router.get("/indicadores", response_model=IndicadoresSalida)
async def indicadores(uow: Uow):
    resultado = await casos_uso.calcular_indicadores(uow)
    return IndicadoresSalida(total=resultado.total, monto_total=resultado.monto_total)


@router.get("/{ejemplo_id}", response_model=EjemploSalida, responses=ERRORES)
async def consultar(ejemplo_id: UUID, uow: Uow):
    return EjemploSalida.desde(await casos_uso.consultar_ejemplo(uow, ejemplo_id))


@router.post("/{ejemplo_id}/aprobacion", response_model=EjemploSalida, responses=ERRORES)
async def aprobar(ejemplo_id: UUID, uow: Uow):
    return EjemploSalida.desde(await casos_uso.aprobar_ejemplo(uow, ejemplo_id))
