from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.application import casos_uso
from app.dependencies import obtener_pasarela, obtener_suscripciones, obtener_uow
from app.ports.externos import PasarelaPagos, VerificadorSuscripcion
from app.ports.persistencia import FabricaUnidadDeTrabajo

from .schemas import CobrarPrimaEntrada, ErrorSalida, PagoSalida

router = APIRouter(prefix="/v1/pagos", tags=["pagos"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Suscripciones = Annotated[VerificadorSuscripcion, Depends(obtener_suscripciones)]
Pasarela = Annotated[PasarelaPagos, Depends(obtener_pasarela)]
ERRORES = {404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}, 503: {"model": ErrorSalida}}


@router.post("/primas", response_model=PagoSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def cobrar_prima(
    entrada: CobrarPrimaEntrada, response: Response, uow: Uow, suscripciones: Suscripciones, pasarela: Pasarela
):
    solicitud = casos_uso.SolicitudCobro(
        solicitud_id=entrada.solicitud_id,
        oferta_id=entrada.oferta_id,
        usuario_id=entrada.usuario_id,
        monto=entrada.monto,
        token_medio_pago=entrada.token_medio_pago,
    )
    resultado = await casos_uso.cobrar_prima(uow, suscripciones, pasarela, solicitud)
    if not resultado.creado:
        response.status_code = status.HTTP_200_OK
    return PagoSalida.desde(resultado.pago)


@router.get("/{pago_id}", response_model=PagoSalida, responses=ERRORES)
async def consultar(pago_id: UUID, uow: Uow):
    return PagoSalida.desde(await casos_uso.consultar_pago(uow, pago_id))
