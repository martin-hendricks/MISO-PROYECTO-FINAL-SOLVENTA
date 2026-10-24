from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status

from app.application import casos_uso
from app.config import Settings
from app.dependencies import obtener_adaptador_open_data, obtener_adaptador_open_finance, obtener_config, obtener_uow
from app.domain.errores import NoEncontrado
from app.ports.adaptadores import AdaptadorOpenData, AdaptadorOpenFinance
from app.ports.persistencia import FabricaUnidadDeTrabajo

from .schemas import (
    ConsentimientoSalida,
    ErrorSalida,
    OfertaSalida,
    OtorgarConsentimientoEntrada,
    SolicitarOfertaEntrada,
)

router = APIRouter(prefix="/v1", tags=["perfilamiento"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
OpenFinance = Annotated[AdaptadorOpenFinance, Depends(obtener_adaptador_open_finance)]
OpenData = Annotated[AdaptadorOpenData, Depends(obtener_adaptador_open_data)]
Config = Annotated[Settings, Depends(obtener_config)]
ERRORES = {403: {"model": ErrorSalida}, 404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.post(
    "/consentimientos",
    response_model=ConsentimientoSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def otorgar_consentimiento(entrada: OtorgarConsentimientoEntrada, response: Response, uow: Uow):
    """HU-53: acción explícita del cliente. No asume nunca consentimiento implícito."""
    registro = await casos_uso.otorgar_consentimiento(uow, entrada.cliente_id)
    if not registro.creado:
        response.status_code = status.HTTP_200_OK
    return ConsentimientoSalida.desde(registro.consentimiento)


@router.get("/consentimientos/{cliente_id}", response_model=ConsentimientoSalida, responses=ERRORES)
async def consultar_consentimiento(cliente_id: str, uow: Uow):
    vigente = await casos_uso.consultar_consentimiento_vigente(uow, cliente_id)
    if vigente is None:
        raise NoEncontrado(f"El cliente {cliente_id} no tiene consentimiento de perfilamiento vigente")
    return ConsentimientoSalida.desde(vigente)


@router.delete("/consentimientos/{cliente_id}", response_model=ConsentimientoSalida, responses=ERRORES)
async def revocar_consentimiento(cliente_id: str, uow: Uow):
    """HU-53: revocar es efectivo de inmediato (sin caché): la siguiente consulta de
    consentimiento vigente ya no lo encuentra."""
    return ConsentimientoSalida.desde(await casos_uso.revocar_consentimiento(uow, cliente_id))


@router.post(
    "/ofertas-hipotecario",
    response_model=OfertaSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def solicitar_oferta_hipotecario(
    entrada: SolicitarOfertaEntrada,
    response: Response,
    uow: Uow,
    adaptador_open_finance: OpenFinance,
    adaptador_open_data: OpenData,
    config: Config,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
):
    """HU-53+HU-54+HU-55+HU-56 en un único flujo: verifica consentimiento, perfila con
    los adaptadores (degradando si hace falta) y arma la oferta explicable."""
    resultado = await casos_uso.perfilar_y_ofertar(
        uow, adaptador_open_finance, adaptador_open_data, config, idempotency_key, entrada.cliente_id
    )
    if not resultado.creada:
        response.status_code = status.HTTP_200_OK
    return OfertaSalida.desde(resultado.oferta)
