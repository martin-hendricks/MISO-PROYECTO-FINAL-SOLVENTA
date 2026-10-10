from fastapi import Request

from app.config import Settings
from app.ports.catalogo import CatalogoProductos
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.riesgo import AdaptadorPerfilRiesgo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_catalogo(request: Request) -> CatalogoProductos:
    return request.app.state.catalogo


def obtener_adaptador_perfil_riesgo(request: Request) -> AdaptadorPerfilRiesgo:
    return request.app.state.adaptador_perfil_riesgo


def obtener_config(request: Request) -> Settings:
    return request.app.state.config
