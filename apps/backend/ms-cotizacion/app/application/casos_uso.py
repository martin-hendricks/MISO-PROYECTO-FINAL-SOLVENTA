from __future__ import annotations

from app.domain.catalogo import DefinicionProducto
from app.domain.errores import ProductoNoEncontrado
from app.ports.catalogo import CatalogoProductos


def consultar_producto(catalogo: CatalogoProductos, producto: str) -> DefinicionProducto:
    definicion = catalogo.obtener(producto)
    if definicion is None:
        raise ProductoNoEncontrado(producto)
    return definicion


def listar_productos(catalogo: CatalogoProductos) -> list[DefinicionProducto]:
    return catalogo.listar()
