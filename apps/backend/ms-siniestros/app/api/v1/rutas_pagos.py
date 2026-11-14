from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.application import casos_uso
from app.dependencies import obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import LlamanteDep, alcance

from .schemas import ErrorSalida
from .schemas_pagos import PagosRecibidosSalida, PagoRecibidoSalida

router = APIRouter(prefix="/v1", tags=["pagos-recibidos"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]


def _dueno(llamante, usuario_id: UUID | None) -> UUID:
    dueno = alcance(llamante, usuario_id)
    if dueno is None:
        raise HTTPException(status_code=422, detail="usuario_id es obligatorio")
    return dueno


@router.get("/pagos-recibidos", response_model=PagosRecibidosSalida)
async def listar_pagos_recibidos(
    uow: Uow,
    llamante: LlamanteDep,
    usuario_id: Annotated[UUID | None, Query()] = None,
):
    """Depósitos ejecutados de un cliente. La regla de inclusión vive en el núcleo."""
    return PagosRecibidosSalida.desde(await casos_uso.listar_pagos_recibidos(uow, _dueno(llamante, usuario_id)))


@router.get(
    "/pagos-recibidos/{siniestro_id}",
    response_model=PagoRecibidoSalida,
    responses={404: {"model": ErrorSalida}},
)
async def obtener_pago_recibido(
    siniestro_id: UUID,
    uow: Uow,
    llamante: LlamanteDep,
    usuario_id: Annotated[UUID | None, Query()] = None,
):
    return PagoRecibidoSalida.desde(
        await casos_uso.obtener_pago_recibido(uow, siniestro_id, _dueno(llamante, usuario_id))
    )
