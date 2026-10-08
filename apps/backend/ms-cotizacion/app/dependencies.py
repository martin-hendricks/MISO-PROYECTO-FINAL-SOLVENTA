from fastapi import Request

from app.ports.catalogo import CatalogoProductos
from app.ports.persistencia import FabricaUnidadDeTrabajo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_catalogo(request: Request) -> CatalogoProductos:
    return request.app.state.catalogo
