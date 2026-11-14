from typing import Annotated

from fastapi import APIRouter, Depends, Header, Response, status

from app.application import casos_uso
from app.config import Settings
from app.dependencies import (
    obtener_adaptador_open_data,
    obtener_adaptador_open_finance,
    obtener_cache_fuentes,
    obtener_config,
    obtener_uow,
)
from app.domain.errores import NoEncontrado
from app.ports.adaptadores import AdaptadorOpenData, AdaptadorOpenFinance
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import LlamanteDep

from .schemas import (
    ConsentimientoSalida,
    ErrorSalida,
    OfertaSalida,
    OriginacionSalida,
    OtorgarConsentimientoEntrada,
    RegistrarOriginacionEntrada,
    SolicitarOfertaEntrada,
)

router = APIRouter(prefix="/v1", tags=["perfilamiento"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
OpenFinance = Annotated[AdaptadorOpenFinance, Depends(obtener_adaptador_open_finance)]
OpenData = Annotated[AdaptadorOpenData, Depends(obtener_adaptador_open_data)]
Config = Annotated[Settings, Depends(obtener_config)]
Cache = Annotated[object, Depends(obtener_cache_fuentes)]
ERRORES = {403: {"model": ErrorSalida}, 404: {"model": ErrorSalida}, 422: {"model": ErrorSalida}}


@router.post(
    "/consentimientos",
    response_model=ConsentimientoSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def otorgar_consentimiento(entrada: OtorgarConsentimientoEntrada, response: Response, uow: Uow, _: LlamanteDep):
    """HU-53: acción explícita del cliente. No asume nunca consentimiento implícito."""
    registro = await casos_uso.otorgar_consentimiento(uow, entrada.cliente_id)
    if not registro.creado:
        response.status_code = status.HTTP_200_OK
    return ConsentimientoSalida.desde(registro.consentimiento)


@router.get("/consentimientos/{cliente_id}", response_model=ConsentimientoSalida, responses=ERRORES)
async def consultar_consentimiento(cliente_id: str, uow: Uow, _: LlamanteDep):
    """Llamada desde bff-web (roles cliente/asesor/operador) y desde
    ms-cotizacion (rol servicio, ver ConsentimientoPerfilamientoHTTP.vigente)."""
    vigente = await casos_uso.consultar_consentimiento_vigente(uow, cliente_id)
    if vigente is None:
        raise NoEncontrado(f"El cliente {cliente_id} no tiene consentimiento de perfilamiento vigente")
    return ConsentimientoSalida.desde(vigente)


@router.delete("/consentimientos/{cliente_id}", response_model=ConsentimientoSalida, responses=ERRORES)
async def revocar_consentimiento(cliente_id: str, uow: Uow, cache: Cache, _: LlamanteDep):
    """HU-53: revocar impide nuevas consultas y reutilizar el perfil cacheado."""
    return ConsentimientoSalida.desde(await casos_uso.revocar_consentimiento(uow, cliente_id, cache))


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
    cache: Cache,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
    _: LlamanteDep,
):
    """HU-53+HU-54+HU-55+HU-56 en un único flujo: verifica consentimiento, perfila con
    los adaptadores (degradando si hace falta) y arma la oferta explicable."""
    resultado = await casos_uso.perfilar_y_ofertar(
        uow,
        adaptador_open_finance,
        adaptador_open_data,
        config,
        idempotency_key,
        entrada.cliente_id,
        cache,
        entrada.numero_documento,
    )
    if not resultado.creada:
        response.status_code = status.HTTP_200_OK
    return OfertaSalida.desde(resultado.oferta)


@router.get("/ofertas-hipotecario/clientes/{cliente_id}/ultima", response_model=OfertaSalida, responses=ERRORES)
async def consultar_ultima_oferta(cliente_id: str, uow: Uow, _: LlamanteDep):
    """IPerfilRiesgo: la última oferta del cliente con su `factor_ajuste`, para que
    ms-cotizacion cotice vida crediticia con el mismo perfil sin volver a perfilar."""
    return OfertaSalida.desde(await casos_uso.consultar_ultima_oferta(uow, cliente_id))


@router.post(
    "/originaciones",
    response_model=OriginacionSalida,
    status_code=status.HTTP_201_CREATED,
    responses=ERRORES,
)
async def registrar_originacion(entrada: RegistrarOriginacionEntrada, uow: Uow, _: LlamanteDep):
    originacion = await casos_uso.registrar_originacion(
        uow, entrada.cliente_id, entrada.valor, entrada.plazo_meses, entrada.origen
    )
    return OriginacionSalida.desde(originacion)


@router.get("/originaciones/clientes/{cliente_id}/pendiente", response_model=OriginacionSalida, responses=ERRORES)
async def consultar_originacion_pendiente(cliente_id: str, uow: Uow, _: LlamanteDep):
    return OriginacionSalida.desde(await casos_uso.consultar_originacion_pendiente(uow, cliente_id))


@router.delete(
    "/originaciones/clientes/{cliente_id}/pendiente",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=ERRORES,
)
async def cerrar_originacion(cliente_id: str, uow: Uow, _: LlamanteDep):
    await casos_uso.cerrar_originacion(uow, cliente_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
