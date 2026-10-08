from typing import Annotated

from fastapi import APIRouter, Depends

from app.application import casos_uso
from app.dependencies import obtener_catalogo
from app.ports.catalogo import CatalogoProductos

from .schemas import ErrorSalida, ProductoSalida

router = APIRouter(prefix="/v1/productos", tags=["productos"])
Catalogo = Annotated[CatalogoProductos, Depends(obtener_catalogo)]


@router.get("", response_model=list[ProductoSalida])
async def listar(catalogo: Catalogo):
    return [ProductoSalida.desde(p) for p in casos_uso.listar_productos(catalogo)]


@router.get("/{producto}", response_model=ProductoSalida, responses={404: {"model": ErrorSalida}})
async def consultar(producto: str, catalogo: Catalogo):
    return ProductoSalida.desde(casos_uso.consultar_producto(catalogo, producto))
