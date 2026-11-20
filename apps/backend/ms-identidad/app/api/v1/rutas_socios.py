from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.application import casos_uso_socios
from app.dependencies import obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import Llamante, exigir_api_socios, exigir_operador

from .schemas import ErrorSalida
from .schemas_socios import (
    ClaveEmitidaSalida,
    CrearSocioEntrada,
    ListaSociosSalida,
    ResolverSocioEntrada,
    SocioCreadoSalida,
    SocioResueltoSalida,
    SocioSalida,
)

router = APIRouter(prefix="/v1/socios", tags=["socios"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Operador = Annotated[Llamante, Depends(exigir_operador)]
ApiSocios = Annotated[Llamante, Depends(exigir_api_socios)]
ERRORES = {
    401: {"model": ErrorSalida},
    403: {"model": ErrorSalida},
    404: {"model": ErrorSalida},
    409: {"model": ErrorSalida},
}


@router.post(
    "",
    response_model=SocioCreadoSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def crear(entrada: CrearSocioEntrada, uow: Uow, _operador: Operador):
    socio, credencial, api_key = await casos_uso_socios.crear_socio(
        uow, entrada.nombre, frozenset(entrada.alcances)
    )
    return SocioCreadoSalida(
        socio_id=socio.socio_id,
        nombre=socio.nombre,
        alcances=sorted(socio.alcances),
        estado=socio.estado.value,
        creado_en=socio.creado_en,
        credencial_id=credencial.credencial_id,
        api_key=api_key,
    )


@router.get("", response_model=ListaSociosSalida, responses=ERRORES)
async def listar(uow: Uow, _operador: Operador):
    return ListaSociosSalida(
        socios=[SocioSalida.desde(s) for s in await casos_uso_socios.listar_socios(uow)]
    )


@router.post("/resolucion", response_model=SocioResueltoSalida, responses=ERRORES)
async def resolver(entrada: ResolverSocioEntrada, uow: Uow, _api_socios: ApiSocios):
    socio = await casos_uso_socios.resolver_por_huella(uow, entrada.huella_sha256)
    return SocioResueltoSalida(
        socio_id=socio.socio_id, nombre=socio.nombre, alcances=sorted(socio.alcances)
    )


@router.post(
    "/{socio_id}/credenciales",
    response_model=ClaveEmitidaSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def emitir_credencial(socio_id: UUID, uow: Uow, _operador: Operador):
    credencial, api_key = await casos_uso_socios.emitir_credencial(uow, socio_id)
    return ClaveEmitidaSalida(credencial_id=credencial.credencial_id, api_key=api_key)


@router.delete(
    "/{socio_id}/credenciales/{credencial_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERRORES,
)
async def revocar_credencial(
    socio_id: UUID, credencial_id: UUID, uow: Uow, _operador: Operador
):
    await casos_uso_socios.revocar_credencial(uow, socio_id, credencial_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{socio_id}/revocacion", response_model=SocioSalida, responses=ERRORES)
async def revocar(socio_id: UUID, uow: Uow, _operador: Operador):
    return SocioSalida.desde(await casos_uso_socios.revocar_socio(uow, socio_id))
