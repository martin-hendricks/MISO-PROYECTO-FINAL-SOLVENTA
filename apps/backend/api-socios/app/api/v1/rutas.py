from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.clients.base import RecursoNoEncontrado
from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.clients.ms_identidad import ClienteMsIdentidad
from app.clients.ms_perfilamiento import ClienteMsPerfilamiento
from app.dependencies import obtener_cliente_cotizacion, obtener_cliente_identidad, obtener_cliente_perfilamiento

from .schemas import CatalogoVista, ErrorVista, OriginacionEntrada, OriginacionVista, ProductoVista

router = APIRouter(prefix="/v1")
Cotizacion = Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)]
Identidad = Annotated[ClienteMsIdentidad, Depends(obtener_cliente_identidad)]
Perfilamiento = Annotated[ClienteMsPerfilamiento, Depends(obtener_cliente_perfilamiento)]
ERRORES = {404: {"model": ErrorVista}, 503: {"model": ErrorVista}}


@router.get(
    "/catalogo",
    response_model=CatalogoVista,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    responses=ERRORES,
)
async def catalogo(cotizacion: Cotizacion):
    return CatalogoVista(productos=[ProductoVista.desde_nucleo(p) for p in await cotizacion.listar_productos()])


@router.get(
    "/catalogo/{codigo}",
    response_model=ProductoVista,
    response_model_by_alias=True,
    response_model_exclude_none=True,
    responses=ERRORES,
)
async def producto(codigo: str, cotizacion: Cotizacion):
    return ProductoVista.desde_nucleo(await cotizacion.obtener_producto(codigo))


@router.post(
    "/originaciones-hipotecarias",
    response_model=OriginacionVista,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
    responses={**ERRORES, 422: {"model": ErrorVista}},
)
async def originar_hipoteca(entrada: OriginacionEntrada, identidad: Identidad, perfilamiento: Perfilamiento):
    """El banco aliado origina el crédito hipotecario de un cliente de Solventa: el
    cliente ve la card Vida hipotecario en Inicio y solo consiente y acepta."""
    try:
        cliente_id = await identidad.usuario_por_documento(entrada.tipo_documento, entrada.numero_documento)
    except RecursoNoEncontrado:
        return JSONResponse(
            status_code=404,
            content={
                "codigo": "cliente_no_registrado",
                "mensaje": "El documento no corresponde a un cliente de Solventa",
            },
        )
    await perfilamiento.registrar_originacion(cliente_id, entrada.valor, entrada.plazo_meses)
    return OriginacionVista(valor=entrada.valor, plazo_meses=entrada.plazo_meses)
