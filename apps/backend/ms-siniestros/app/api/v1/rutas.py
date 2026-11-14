from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.application import avisos, casos_uso
from app.dependencies import obtener_adaptador_desembolso, obtener_uow
from app.domain.modelos import EstadoSiniestro, ResultadoDecision, TipoSiniestro
from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import FabricaUnidadDeTrabajo, FiltroSiniestros
from app.seguridad import LlamanteDep, alcance

from .schemas import (
    CambiarEstadoEntrada,
    ErrorSalida,
    EventoParametricoEntrada,
    ResultadoIngestaSalida,
    SiniestrosAbiertosSalida,
    SiniestroSalida,
)

router = APIRouter(prefix="/v1", tags=["siniestros"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Desembolso = Annotated[AdaptadorDesembolso, Depends(obtener_adaptador_desembolso)]
ERRORES = {404: {"model": ErrorSalida}, 409: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.post(
    "/eventos-parametricos",
    response_model=ResultadoIngestaSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def ingerir_evento_parametrico(
    entrada: EventoParametricoEntrada,
    response: Response,
    uow: Uow,
    adaptador_desembolso: Desembolso,
    llamante: LlamanteDep,
):
    if llamante.rol == "cliente":
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Rol no autorizado")
    """HU-32 + HU-33 + HU-34: ingiere el evento paramétrico simulado, encadena la
    evaluación del umbral y, si corresponde, dispara el pago paramétrico stub."""
    resultado = await casos_uso.recibir_evento_parametrico(
        uow,
        adaptador_desembolso,
        entrada.evento_id,
        entrada.valor,
        entrada.umbral,
        entrada.poliza_vigente,
        entrada.monto_pago,
        entrada.poliza_id,
        entrada.usuario_id,
        entrada.ramo,
        entrada.poliza_numero,
        entrada.descripcion,
    )
    if not resultado.procesado:
        response.status_code = status.HTTP_200_OK
    return ResultadoIngestaSalida.desde(resultado)


@router.get("/siniestros", response_model=list[SiniestroSalida])
async def listar_siniestros(
    uow: Uow,
    llamante: LlamanteDep,
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
    usuario_id: UUID | None = None,
    tipo: TipoSiniestro | None = None,
    estado: EstadoSiniestro | None = None,
    resultado: ResultadoDecision | None = None,
    requiere_revision: bool | None = None,
):
    """usuario_id = "Mis siniestros" (HU-160): un cliente solo ve lo suyo aunque no lo
    envíe (alcance). requiere_revision/resultado = chips de la cola del operador (HU-26)."""
    filtro = FiltroSiniestros(
        usuario_id=alcance(llamante, usuario_id),
        tipo=tipo,
        estado=estado,
        resultado=resultado,
        requiere_revision=requiere_revision,
        limite=limite,
    )
    return [SiniestroSalida.desde(s) for s in await avisos.filtrar(uow, filtro)]


# Prefijo literal antes de "/siniestros/{siniestro_id}": mismo motivo que
# ms-polizas documenta en /numero/{numero} (FastAPI resuelve rutas en orden
# de registro; "abiertos" no debe intentarse parsear como UUID).
@router.get("/siniestros/abiertos", response_model=SiniestrosAbiertosSalida)
async def listar_siniestros_abiertos(uow: Uow, llamante: LlamanteDep, poliza_id: UUID):
    if llamante.rol == "cliente":
        raise HTTPException(status_code=403, detail="Rol no autorizado")
    """HU-61 (back-office): usado por ms-polizas/bff-web antes de cancelar
    una póliza, solo como dato informativo -- no bloquea la cancelación."""
    siniestros = await casos_uso.listar_siniestros_abiertos_de_poliza(uow, poliza_id)
    return SiniestrosAbiertosSalida(abiertos=len(siniestros), siniestros=[SiniestroSalida.desde(s) for s in siniestros])


@router.get("/siniestros/{siniestro_id}", response_model=SiniestroSalida, responses=ERRORES)
async def consultar_siniestro(
    siniestro_id: UUID, uow: Uow, llamante: LlamanteDep, usuario_id: UUID | None = None
):
    """HU-30: lectura del estado único del siniestro, la misma fuente que leerían todos
    los canales (cola del operador, decisión, pago, lista del cliente)."""
    dueno = llamante.uid if llamante.rol == "cliente" else usuario_id
    return SiniestroSalida.desde(await casos_uso.consultar_siniestro(uow, siniestro_id, dueno))


@router.post("/siniestros/{siniestro_id}/estado", response_model=SiniestroSalida, responses=ERRORES)
async def cambiar_estado(siniestro_id: UUID, entrada: CambiarEstadoEntrada, uow: Uow, llamante: LlamanteDep):
    if llamante.rol == "cliente":
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Rol no autorizado")
    """HU-30: aplica una transición de estado explícita. Una transición inválida se
    rechaza con 409 y el siniestro conserva su estado anterior."""
    siniestro = await casos_uso.cambiar_estado_siniestro(uow, siniestro_id, entrada.estado, entrada.origen)
    return SiniestroSalida.desde(siniestro)
