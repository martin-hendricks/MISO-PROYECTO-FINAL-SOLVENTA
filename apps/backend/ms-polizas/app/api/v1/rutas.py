from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.application import casos_uso
from app.dependencies import obtener_cobros, obtener_suscripciones, obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.precondiciones import VerificadorCobro, VerificadorSuscripcion

from .schemas import EmitirPolizaEntrada, ErrorSalida, PolizaSalida

router = APIRouter(prefix="/v1/polizas", tags=["polizas"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Suscripciones = Annotated[VerificadorSuscripcion, Depends(obtener_suscripciones)]
Cobros = Annotated[VerificadorCobro, Depends(obtener_cobros)]
ERRORES = {404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}, 503: {"model": ErrorSalida}}


@router.post("", response_model=PolizaSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def emitir(
    entrada: EmitirPolizaEntrada, response: Response, uow: Uow, suscripciones: Suscripciones, cobros: Cobros
):
    solicitud = casos_uso.SolicitudEmision(
        solicitud_id=entrada.solicitud_id,
        oferta_id=entrada.oferta_id,
        usuario_id=entrada.usuario_id,
        token_pago_confirmado=entrada.token_pago_confirmado,
        coberturas=[c.a_dominio() for c in entrada.coberturas],
    )
    resultado = await casos_uso.emitir_poliza(uow, suscripciones, cobros, solicitud)
    if not resultado.creada:
        response.status_code = status.HTTP_200_OK
    return PolizaSalida.desde(resultado.poliza)


@router.get("/{poliza_id}", response_model=PolizaSalida, responses=ERRORES)
async def consultar(poliza_id: UUID, uow: Uow):
    return PolizaSalida.desde(await casos_uso.consultar_poliza(uow, poliza_id))
