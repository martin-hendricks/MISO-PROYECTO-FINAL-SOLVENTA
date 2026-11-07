from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.exceptions import RequestValidationError

from app.application import casos_uso
from app.dependencies import (
    obtener_cobros,
    obtener_firma,
    obtener_reportes,
    obtener_suscripciones,
    obtener_uow,
    obtener_uow_lectura,
)
from app.ports.firma import FirmaElectronica
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.precondiciones import VerificadorCobro, VerificadorSuscripcion
from app.ports.reportes import GeneradorReportes
from app.seguridad import LlamanteDep, alcance
from app.domain.errores import NoEncontrado

from .schemas import (
    CancelarPolizaEntrada,
    ConstanciaFirmaSalida,
    EmitirPolizaEntrada,
    ErrorSalida,
    ModificarCoberturasEntrada,
    OfertasConPolizaSalida,
    PolizaSalida,
    PreferenciaPolizaEntrada,
    ReporteSalida,
    RenovarPolizaEntrada,
)

router = APIRouter(prefix="/v1/polizas", tags=["polizas"])
router_reportes = APIRouter(prefix="/v1/reportes", tags=["reportes"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
# EC-LAT-10: los endpoints de solo consulta leen de la réplica (ver
# obtener_uow_lectura), no del writer que usa el resto de la ruta.
UowLectura = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow_lectura)]
Suscripciones = Annotated[VerificadorSuscripcion, Depends(obtener_suscripciones)]
Cobros = Annotated[VerificadorCobro, Depends(obtener_cobros)]
Firma = Annotated[FirmaElectronica, Depends(obtener_firma)]
Reportes = Annotated[GeneradorReportes, Depends(obtener_reportes)]
ERRORES = {404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}, 503: {"model": ErrorSalida}}
ERRORES_CICLO_VIDA = {**ERRORES, 409: {"model": ErrorSalida}}
ERRORES_REPORTES = {403: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}
MAX_OFERTAS_POR_CONSULTA = 100


def _exigir_operador(llamante) -> None:
    """HU-62/HU-63: el Gherkin pide roles "compliance"/"operations", que no
    existen en este sistema (seguridad.ROLES = cliente/asesor/operador) --
    se autorizan contra "operador", el único rol de back-office real. Misma
    decisión ya tomada en bff-web para estos mismos endpoints."""
    if llamante.rol != "operador":
        raise HTTPException(status_code=403, detail="Rol no autorizado")


@router.post("", response_model=PolizaSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def emitir(
    entrada: EmitirPolizaEntrada,
    response: Response,
    uow: Uow,
    suscripciones: Suscripciones,
    cobros: Cobros,
    firma: Firma,
    llamante: LlamanteDep,
):
    if llamante.rol == "cliente" and entrada.usuario_id != llamante.uid:
        raise NoEncontrado("La póliza no existe")
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
async def listar(
    uow: UowLectura, llamante: LlamanteDep, usuario_id: UUID, limite: Annotated[int, Query(ge=1, le=100)] = 20
):
    polizas = await casos_uso.listar_polizas_de_usuario(uow, alcance(llamante, usuario_id), limite)
    return [PolizaSalida.desde(poliza) for poliza in polizas]


# Ruta registrada antes de "/{poliza_id}": FastAPI resuelve rutas en orden de
# registro, y el prefijo literal "/numero/" es inequívoco frente al
# path-param UUID de abajo (si "/{poliza_id}" se registrara primero, FastAPI
# intentaría parsear "numero" como UUID y fallaría con 422 en vez de llegar
# aquí).
@router.get("/numero/{numero}", response_model=PolizaSalida, responses=ERRORES)
async def consultar_por_numero(
    numero: str, uow: UowLectura, llamante: LlamanteDep, usuario_id: UUID | None = None
):
    return PolizaSalida.desde(
        await casos_uso.consultar_poliza_por_numero(uow, numero, alcance(llamante, usuario_id))
    )


# Igual que "/numero/": el prefijo literal "/firmas/" va antes de "/{poliza_id}".
# Lee del writer, no de la réplica: el flujo consulta la firma justo después
# de emitir y no debe ver un estado atrasado (HU-17).
@router.get("/firmas/{oferta_id}", response_model=ConstanciaFirmaSalida, responses=ERRORES)
async def consultar_firma(oferta_id: UUID, uow: Uow):
    return ConstanciaFirmaSalida.desde(await casos_uso.consultar_firma(uow, oferta_id))


# HU-163: bff-web cruza las cotizaciones aceptadas del asesor con las pólizas ya
# emitidas. Prefijo literal antes de "/{poliza_id}", igual que "/numero/".
@router.get("/por-ofertas", response_model=OfertasConPolizaSalida, responses=ERRORES)
async def ofertas_con_poliza(uow: UowLectura, oferta_ids: Annotated[str, Query(min_length=1)]):
    try:
        ids = [UUID(valor.strip()) for valor in oferta_ids.split(",")]
    except ValueError as exc:
        raise RequestValidationError([{"loc": ("query", "oferta_ids"), "msg": "UUID inválido", "type": "uuid_parsing"}]) from exc
    if len(ids) > MAX_OFERTAS_POR_CONSULTA:
        raise RequestValidationError(
            [{"loc": ("query", "oferta_ids"), "msg": f"Máximo {MAX_OFERTAS_POR_CONSULTA} ids", "type": "too_long"}]
        )
    return OfertasConPolizaSalida(oferta_ids_con_poliza=await casos_uso.ofertas_con_poliza(uow, ids))


# HU-119: prefijo literal antes de "/{poliza_id}", igual que "/numero/",
# "/firmas/" y "/por-ofertas" arriba -- FastAPI resuelve en orden de
# registro y "/{poliza_id}" (UUID) capturaría "por-vencer" como path param
# si se registrara antes.
@router.get("/por-vencer", response_model=list[PolizaSalida], responses=ERRORES)
async def por_vencer(
    uow: UowLectura,
    llamante: LlamanteDep,
    usuario_id: UUID | None = None,
    dias: Annotated[int, Query(ge=1, le=365)] = casos_uso.DIAS_AVISO_VENCIMIENTO_DEFECTO,
):
    polizas = await casos_uso.listar_polizas_por_vencer(uow, alcance(llamante, usuario_id), dias)
    return [PolizaSalida.desde(poliza) for poliza in polizas]


@router.get("/{poliza_id}", response_model=PolizaSalida, responses=ERRORES)
async def consultar(poliza_id: UUID, uow: UowLectura, llamante: LlamanteDep):
    poliza = await casos_uso.consultar_poliza(uow, poliza_id)
    if llamante.rol == "cliente" and poliza.usuario_id != llamante.uid:
        raise NoEncontrado(f"La póliza {poliza_id} no existe")
    return PolizaSalida.desde(poliza)


@router.post("/{poliza_id}/renovacion", response_model=PolizaSalida, responses=ERRORES_CICLO_VIDA)
async def renovar(poliza_id: UUID, entrada: RenovarPolizaEntrada, uow: Uow):
    poliza = await casos_uso.renovar_poliza(uow, poliza_id, entrada.nueva_fin_vigencia)
    return PolizaSalida.desde(poliza)


@router.post("/{poliza_id}/coberturas", response_model=PolizaSalida, responses=ERRORES_CICLO_VIDA)
async def modificar_coberturas(poliza_id: UUID, entrada: ModificarCoberturasEntrada, uow: Uow):
    poliza = await casos_uso.modificar_poliza(uow, poliza_id, [c.a_dominio() for c in entrada.coberturas])
    return PolizaSalida.desde(poliza)


@router.patch("/{poliza_id}/preferencias", response_model=PolizaSalida, responses=ERRORES)
async def preferencias(poliza_id: UUID, entrada: PreferenciaPolizaEntrada, uow: Uow, usuario_id: UUID | None = None):
    poliza = await casos_uso.guardar_renovacion_automatica(
        uow, poliza_id, entrada.renovacion_automatica, usuario_id
    )
    return PolizaSalida.desde(poliza)


@router.post("/{poliza_id}/cancelacion", response_model=PolizaSalida, responses=ERRORES_CICLO_VIDA)
async def cancelar(poliza_id: UUID, entrada: CancelarPolizaEntrada, uow: Uow):
    poliza = await casos_uso.cancelar_poliza(uow, poliza_id, entrada.motivo, entrada.operador)
    return PolizaSalida.desde(poliza)


@router_reportes.get("/regulador", response_model=ReporteSalida, responses=ERRORES_REPORTES)
async def reporte_regulador(
    uow: UowLectura, reportes: Reportes, llamante: LlamanteDep, desde: date, hasta: date
):
    _exigir_operador(llamante)
    reporte = await casos_uso.generar_reporte_regulador(uow, reportes, desde, hasta)
    return ReporteSalida(**vars(reporte))


@router_reportes.get("/reaseguradora", response_model=ReporteSalida, responses=ERRORES_REPORTES)
async def reporte_reaseguradora(
    uow: UowLectura, reportes: Reportes, llamante: LlamanteDep, desde: date, hasta: date
):
    _exigir_operador(llamante)
    reporte = await casos_uso.generar_reporte_reaseguradora(uow, reportes, desde, hasta)
    return ReporteSalida(**vars(reporte))
