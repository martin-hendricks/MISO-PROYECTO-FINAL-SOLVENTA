from typing import Annotated

from fastapi import APIRouter, Depends

from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.dependencies import obtener_cliente_cotizacion

from .schemas import CatalogoVista, ErrorVista, ProductoVista

# Contrato versionado de solo lectura para socios (HU-2). La credencial de socio
# (requiere_rol("socio") de solventa_seguridad) se agrega en este router cuando entre HU-76.
router = APIRouter(prefix="/v1")
Cotizacion = Annotated[ClienteMsCotizacion, Depends(obtener_cliente_cotizacion)]
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
