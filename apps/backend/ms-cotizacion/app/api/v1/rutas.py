from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status

from app.application import casos_uso
from app.dependencies import obtener_catalogo, obtener_uow
from app.ports.catalogo import CatalogoProductos
from app.ports.persistencia import FabricaUnidadDeTrabajo

from .schemas import CotizacionSalida, ErrorSalida, SolicitarCotizacionEntrada

router = APIRouter(prefix="/v1/cotizaciones", tags=["cotizaciones"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Catalogo = Annotated[CatalogoProductos, Depends(obtener_catalogo)]
ERRORES = {422: {"model": ErrorSalida}}


@router.post("", response_model=CotizacionSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def recibir_solicitud(
    entrada: SolicitarCotizacionEntrada,
    response: Response,
    uow: Uow,
    catalogo: Catalogo,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
):
    resultado = await casos_uso.recibir_solicitud(
        uow,
        catalogo,
        idempotency_key,
        entrada.usuario_id,
        entrada.socio_id,
        entrada.consentimiento_id,
        entrada.producto,
        entrada.canal,
        entrada.datos_riesgo,
    )
    if not resultado.creada:
        response.status_code = status.HTTP_200_OK
    return CotizacionSalida.desde(resultado.solicitud)
