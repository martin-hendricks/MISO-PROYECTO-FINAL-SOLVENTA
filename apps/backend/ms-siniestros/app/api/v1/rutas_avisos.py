"""Rutas del siniestro asistido (HU-157): alta con evidencia, detalle, cola del operador,
decisión, perito, pago de bajo monto y parametría."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Response, UploadFile, status
from pydantic import ValidationError

from app.application import avisos
from app.config import Settings
from app.dependencies import (
    obtener_adaptador_desembolso,
    obtener_almacen_evidencias,
    obtener_config,
    obtener_uow,
)
from app.domain.aviso import ArchivoEvidencia
from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import ResultadoDecision
from app.ports.evidencias import AlmacenEvidencias
from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import LlamanteDep, dueno_visible, exigir_rol

from .schemas import ErrorSalida
from .schemas_avisos import (
    AvisoEntrada,
    DecisionEntrada,
    DetalleSalida,
    EvaluacionPendientesSalida,
    PagoEntrada,
    PagoRealizadoSalida,
    ParametroRamoSalida,
    PeritoEntrada,
)

router = APIRouter(prefix="/v1", tags=["siniestro-asistido"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Almacen = Annotated[AlmacenEvidencias, Depends(obtener_almacen_evidencias)]
Desembolso = Annotated[AdaptadorDesembolso, Depends(obtener_adaptador_desembolso)]
Config = Annotated[Settings, Depends(obtener_config)]
ERRORES = {
    404: {"model": ErrorSalida},
    409: {"model": ErrorSalida},
    422: {"model": ErrorSalida},
    503: {"model": ErrorSalida},
}


@router.post("/siniestros", response_model=DetalleSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def registrar_aviso(
    response: Response,
    uow: Uow,
    almacen: Almacen,
    config: Config,
    llamante: LlamanteDep,
    datos: Annotated[str, Form(description="JSON con AvisoEntrada")],
    archivos: Annotated[list[UploadFile], File(description="Evidencia: PNG, JPG, PDF o MP4, máx. 10 MB c/u")],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key", max_length=120)] = None,
):
    """N5 + N6: alta del aviso con su evidencia. Responde RECIBIDO de inmediato; el motor
    evalúa después (asíncrono). Con el mismo Idempotency-Key un reintento devuelve el aviso
    original con 200, sin duplicarlo."""
    try:
        entrada = AvisoEntrada.model_validate_json(datos)
    except ValidationError as exc:
        raise ReglaDeNegocioViolada("aviso_invalido", f"Datos del aviso inválidos: {exc.errors()[0]['msg']}") from exc
    # Solo el cliente avisa, y solo a su nombre: el usuario_id del cuerpo debe ser el del token.
    if llamante.rol != "cliente" or llamante.uid != entrada.usuario_id:
        raise HTTPException(status_code=404, detail="No existe")

    evidencia = []
    for indice, archivo in enumerate(archivos):
        tipo = entrada.tipos_adjuntos[indice] if indice < len(entrada.tipos_adjuntos) else "documento"
        evidencia.append(
            ArchivoEvidencia(
                nombre=archivo.filename or "evidencia",
                content_type=(archivo.content_type or "").split(";")[0].strip().lower(),
                contenido=await archivo.read(),
                tipo=tipo,
            )
        )

    detalle, creado = await avisos.registrar_aviso(
        uow,
        almacen,
        usuario_id=entrada.usuario_id,
        poliza=entrada.poliza.a_dominio(),
        fecha_hecho=entrada.fecha_hecho,
        descripcion=entrada.descripcion,
        canal=entrada.canal,
        geo=entrada.geo.a_dominio() if entrada.geo else None,
        archivos=evidencia,
        clave_idempotencia=idempotency_key,
    )
    if not creado:
        response.status_code = status.HTTP_200_OK
    return await DetalleSalida.desde(detalle, almacen, config.url_evidencia_expira_segundos)


# Literal antes de /siniestros/{siniestro_id}/...: mismo motivo que /siniestros/abiertos.
@router.post("/siniestros/evaluaciones-pendientes", response_model=EvaluacionPendientesSalida)
async def evaluar_pendientes(
    uow: Uow,
    desembolso: Desembolso,
    llamante: LlamanteDep,
    limite: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """Dispara una pasada del motor sin esperar al worker (operación y pruebas E2E)."""
    exigir_rol(llamante, "operador")
    return EvaluacionPendientesSalida(procesados=await avisos.evaluar_pendientes(uow, desembolso, limite))


@router.get("/siniestros/{siniestro_id}/detalle", response_model=DetalleSalida, responses=ERRORES)
async def detalle(
    siniestro_id: UUID,
    uow: Uow,
    almacen: Almacen,
    config: Config,
    llamante: LlamanteDep,
    usuario_id: UUID | None = None,
):
    """Detalle con evidencia (URLs firmadas temporales), decisiones auditadas y pago. Un
    cliente solo ve los suyos: uno ajeno responde 404, igual que uno inexistente."""
    resultado = await avisos.consultar_detalle(uow, siniestro_id, dueno_visible(llamante, usuario_id))
    return await DetalleSalida.desde(resultado, almacen, config.url_evidencia_expira_segundos)


@router.post("/siniestros/{siniestro_id}/decision", response_model=DetalleSalida, responses=ERRORES)
async def decidir(
    siniestro_id: UUID, entrada: DecisionEntrada, uow: Uow, almacen: Almacen, config: Config, llamante: LlamanteDep
):
    """HU-27: aprobar o rechazar con auditoría. Rechazar sin motivo -> 422."""
    exigir_rol(llamante, "operador")
    resultado = await avisos.decidir_por_operador(
        uow, siniestro_id, ResultadoDecision(entrada.resultado), entrada.motivo, _actor(llamante, entrada.actor)
    )
    return await DetalleSalida.desde(resultado, almacen, config.url_evidencia_expira_segundos)


@router.post("/siniestros/{siniestro_id}/perito", response_model=DetalleSalida, responses=ERRORES)
async def enrutar_a_perito(
    siniestro_id: UUID, entrada: PeritoEntrada, uow: Uow, almacen: Almacen, config: Config, llamante: LlamanteDep
):
    """HU-28: enruta el caso a un perito (estado enrutado)."""
    exigir_rol(llamante, "operador")
    resultado = await avisos.enrutar_a_perito(uow, siniestro_id, entrada.motivo, _actor(llamante, entrada.actor))
    return await DetalleSalida.desde(resultado, almacen, config.url_evidencia_expira_segundos)


@router.post(
    "/siniestros/{siniestro_id}/pago",
    response_model=PagoRealizadoSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def pagar(
    siniestro_id: UUID,
    entrada: PagoEntrada,
    response: Response,
    uow: Uow,
    almacen: Almacen,
    desembolso: Desembolso,
    config: Config,
    llamante: LlamanteDep,
):
    """HU-29: pago de bajo monto, una sola vez. Reintento -> 200 con el mismo comprobante."""
    exigir_rol(llamante, "operador")
    resultado = await avisos.pagar_siniestro(uow, desembolso, siniestro_id, _actor(llamante, entrada.actor))
    if resultado.reintento:
        response.status_code = status.HTTP_200_OK
    return await PagoRealizadoSalida.desde(resultado, almacen, config.url_evidencia_expira_segundos)


@router.get("/parametros-ramo", response_model=list[ParametroRamoSalida])
async def parametros(uow: Uow, _llamante: LlamanteDep):
    """Parametría por ramo: reserva y umbral de aprobación automática."""
    return [ParametroRamoSalida.desde(p) for p in await avisos.listar_parametros(uow)]


def _actor(llamante, declarado: str) -> str:
    """La auditoría usa la identidad del token; el actor del cuerpo solo si el token no la trae."""
    return llamante.sub or declarado
