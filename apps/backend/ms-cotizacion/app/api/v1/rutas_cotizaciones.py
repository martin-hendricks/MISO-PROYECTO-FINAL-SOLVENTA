from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response, status

from app.application import casos_uso_cotizaciones as casos_uso
from app.config import Settings
from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import EstadoSolicitud
from app.dependencies import (
    obtener_adaptador_perfil_riesgo,
    obtener_catalogo,
    obtener_config,
    obtener_suscripciones,
    obtener_uow,
)
from app.ports.catalogo import CatalogoProductos
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.riesgo import AdaptadorPerfilRiesgo
from app.ports.suscripcion import MotorSuscripcion

from .schemas_cotizaciones import (
    AceptacionSalida,
    AceptarOfertaEntrada,
    CotizacionSalida,
    ErrorSalida,
    PaginaCotizacionesAsesorSalida,
    SolicitarCotizacionEntrada,
)

router = APIRouter(prefix="/v1/cotizaciones", tags=["cotizaciones"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Catalogo = Annotated[CatalogoProductos, Depends(obtener_catalogo)]
AdaptadorRiesgo = Annotated[AdaptadorPerfilRiesgo, Depends(obtener_adaptador_perfil_riesgo)]
Config = Annotated[Settings, Depends(obtener_config)]
Suscripciones = Annotated[MotorSuscripcion, Depends(obtener_suscripciones)]
ERRORES = {404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.post("", response_model=CotizacionSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def solicitar_cotizacion(
    entrada: SolicitarCotizacionEntrada,
    response: Response,
    uow: Uow,
    catalogo: Catalogo,
    adaptador_riesgo: AdaptadorRiesgo,
    config: Config,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
):
    resultado = await casos_uso.cotizar(
        uow,
        catalogo,
        adaptador_riesgo,
        config,
        idempotency_key,
        entrada.usuario_id,
        entrada.socio_id,
        entrada.consentimiento_id,
        entrada.producto,
        entrada.canal,
        entrada.datos_riesgo,
        asesor_id=entrada.asesor_id,
        cliente_ref=entrada.cliente_ref,
    )
    if not resultado.creada:
        response.status_code = status.HTTP_200_OK
    return CotizacionSalida.desde(resultado.solicitud, resultado.oferta)


def _estados(valor: str) -> frozenset[EstadoSolicitud]:
    try:
        return frozenset(EstadoSolicitud(e.strip()) for e in valor.split(",") if e.strip())
    except ValueError as exc:
        raise ReglaDeNegocioViolada("estado_invalido", f"Estado desconocido en '{valor}'") from exc


@router.get("", response_model=PaginaCotizacionesAsesorSalida, responses={422: {"model": ErrorSalida}})
async def listar_cotizaciones_asesor(
    uow: Uow,
    asesor_id: UUID,
    estados: str = "cotizada,aceptada",
    incluir_vencidas: bool = False,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamano: Annotated[int, Query(ge=1, le=100)] = 20,
):
    """HU-163: cotizaciones que creó el asesor desde el back-office. Las creadas sin
    asesor_id (canal socio o anteriores a HU-163) nunca se listan."""
    resultado = await casos_uso.listar_cotizaciones_asesor(
        uow, asesor_id, _estados(estados), incluir_vencidas, pagina, tamano
    )
    return PaginaCotizacionesAsesorSalida.desde(resultado)


@router.get("/{cotizacion_id}", response_model=CotizacionSalida, responses={404: {"model": ErrorSalida}})
async def reconsultar_oferta(cotizacion_id: UUID, uow: Uow):
    resultado = await casos_uso.reconsultar_oferta(uow, cotizacion_id)
    return CotizacionSalida.desde_consulta(resultado.solicitud, resultado.consulta)


# Registrada antes de "/{cotizacion_id}/aceptacion" no hace falta (prefijos
# distintos, "por-oferta" nunca calza con un UUID), pero el orden de registro
# en FastAPI sí importa frente a cualquier futura ruta GET "/{cotizacion_id}/
# algo": este prefijo literal es inequívoco porque nunca es un UUID válido.
@router.get(
    "/por-oferta/{oferta_id}", response_model=CotizacionSalida, responses={404: {"model": ErrorSalida}}
)
async def reconsultar_oferta_por_id(oferta_id: UUID, uow: Uow):
    """Resuelve el producto real de una oferta ya aceptada/emitida a partir
    de su oferta_id -- lo único que ms-polizas guarda de la cotización
    original (no guarda cotizacion_id). Usado por bff-web en billetera()/
    detalle() para no mostrar un placeholder de ramo."""
    resultado = await casos_uso.reconsultar_oferta_por_id(uow, oferta_id)
    return CotizacionSalida.desde_consulta(resultado.solicitud, resultado.consulta)


@router.post(
    "/{cotizacion_id}/aceptacion",
    response_model=AceptacionSalida,
    status_code=status.HTTP_201_CREATED,
    responses={**ERRORES, 503: {"model": ErrorSalida}},
)
async def aceptar_oferta(
    cotizacion_id: UUID,
    entrada: AceptarOfertaEntrada,
    response: Response,
    uow: Uow,
    suscripciones: Suscripciones,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
):
    resultado = await casos_uso.aceptar_oferta(
        uow, suscripciones, cotizacion_id, idempotency_key, entrada.perfil_id, entrada.score
    )
    if not resultado.creada:
        response.status_code = status.HTTP_200_OK
    return AceptacionSalida.desde(resultado)
