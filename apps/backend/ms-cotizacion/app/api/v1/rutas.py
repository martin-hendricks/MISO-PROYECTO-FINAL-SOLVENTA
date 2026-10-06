from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.application import casos_uso
from app.application.casos_uso import Colaboradores
from app.dependencies import obtener_colaboradores

from .schemas import CotizacionSalida, ErrorSalida, SolicitudCotizacionEntrada

router = APIRouter(prefix="/v1/cotizaciones", tags=["cotizaciones"])
Deps = Annotated[Colaboradores, Depends(obtener_colaboradores)]


@router.post(
    "",
    response_model=CotizacionSalida,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ErrorSalida}},
)
async def recibir_solicitud(entrada: SolicitudCotizacionEntrada, deps: Deps):
    """HU-3: recibe producto y datos mínimos del riesgo y devuelve la oferta con su cotizacionId."""
    cotizacion = await casos_uso.recibir_solicitud(deps, entrada.producto, entrada.datos_riesgo)
    return CotizacionSalida.desde(cotizacion)
