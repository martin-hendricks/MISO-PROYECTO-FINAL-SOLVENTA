from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.application import casos_uso
from app.dependencies import (
    obtener_cobros,
    obtener_firma,
    obtener_suscripciones,
    obtener_uow,
    obtener_uow_lectura,
)
from app.ports.firma import FirmaElectronica
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.precondiciones import VerificadorCobro, VerificadorSuscripcion

from .schemas import (
    CancelarPolizaEntrada,
    ConstanciaFirmaSalida,
    EmitirPolizaEntrada,
    ErrorSalida,
    ModificarCoberturasEntrada,
    PolizaSalida,
    RenovarPolizaEntrada,
)

router = APIRouter(prefix="/v1/polizas", tags=["polizas"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
# EC-LAT-10: los endpoints de solo consulta leen de la réplica (ver
# obtener_uow_lectura), no del writer que usa el resto de la ruta.
UowLectura = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow_lectura)]
Suscripciones = Annotated[VerificadorSuscripcion, Depends(obtener_suscripciones)]
Cobros = Annotated[VerificadorCobro, Depends(obtener_cobros)]
Firma = Annotated[FirmaElectronica, Depends(obtener_firma)]
ERRORES = {404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}, 503: {"model": ErrorSalida}}
ERRORES_CICLO_VIDA = {**ERRORES, 409: {"model": ErrorSalida}}


@router.post("", response_model=PolizaSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def emitir(
    entrada: EmitirPolizaEntrada,
    response: Response,
    uow: Uow,
    suscripciones: Suscripciones,
    cobros: Cobros,
    firma: Firma,
):
    solicitud = casos_uso.SolicitudEmision(
        solicitud_id=entrada.solicitud_id,
        oferta_id=entrada.oferta_id,
        usuario_id=entrada.usuario_id,
        token_pago_confirmado=entrada.token_pago_confirmado,
        coberturas=[c.a_dominio() for c in entrada.coberturas],
    )
    resultado = await casos_uso.emitir_poliza(uow, suscripciones, cobros, firma, solicitud)
    if not resultado.creada:
        response.status_code = status.HTTP_200_OK
    return PolizaSalida.desde(resultado.poliza)


@router.get("", response_model=list[PolizaSalida], responses=ERRORES)
async def listar(uow: UowLectura, usuario_id: UUID, limite: Annotated[int, Query(ge=1, le=100)] = 20):
    polizas = await casos_uso.listar_polizas_de_usuario(uow, usuario_id, limite)
    return [PolizaSalida.desde(poliza) for poliza in polizas]


# Ruta registrada antes de "/{poliza_id}": FastAPI resuelve rutas en orden de
# registro, y el prefijo literal "/numero/" es inequívoco frente al
# path-param UUID de abajo (si "/{poliza_id}" se registrara primero, FastAPI
# intentaría parsear "numero" como UUID y fallaría con 422 en vez de llegar
# aquí).
@router.get("/numero/{numero}", response_model=PolizaSalida, responses=ERRORES)
async def consultar_por_numero(numero: str, uow: UowLectura):
    return PolizaSalida.desde(await casos_uso.consultar_poliza_por_numero(uow, numero))


# Igual que "/numero/": el prefijo literal "/firmas/" va antes de "/{poliza_id}".
# Lee del writer, no de la réplica: el flujo consulta la firma justo después
# de emitir y no debe ver un estado atrasado (HU-17).
@router.get("/firmas/{oferta_id}", response_model=ConstanciaFirmaSalida, responses=ERRORES)
async def consultar_firma(oferta_id: UUID, uow: Uow):
    return ConstanciaFirmaSalida.desde(await casos_uso.consultar_firma(uow, oferta_id))


@router.get("/{poliza_id}", response_model=PolizaSalida, responses=ERRORES)
async def consultar(poliza_id: UUID, uow: UowLectura):
    return PolizaSalida.desde(await casos_uso.consultar_poliza(uow, poliza_id))


@router.post("/{poliza_id}/renovacion", response_model=PolizaSalida, responses=ERRORES_CICLO_VIDA)
async def renovar(poliza_id: UUID, entrada: RenovarPolizaEntrada, uow: Uow):
    poliza = await casos_uso.renovar_poliza(uow, poliza_id, entrada.nueva_fin_vigencia)
    return PolizaSalida.desde(poliza)


@router.post("/{poliza_id}/coberturas", response_model=PolizaSalida, responses=ERRORES_CICLO_VIDA)
async def modificar_coberturas(poliza_id: UUID, entrada: ModificarCoberturasEntrada, uow: Uow):
    poliza = await casos_uso.modificar_poliza(uow, poliza_id, [c.a_dominio() for c in entrada.coberturas])
    return PolizaSalida.desde(poliza)


@router.post("/{poliza_id}/cancelacion", response_model=PolizaSalida, responses=ERRORES_CICLO_VIDA)
async def cancelar(poliza_id: UUID, entrada: CancelarPolizaEntrada, uow: Uow):
    poliza = await casos_uso.cancelar_poliza(uow, poliza_id, entrada.motivo)
    return PolizaSalida.desde(poliza)
