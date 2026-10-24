from fastapi import Request

from app.config import Settings
from app.ports.adaptadores import AdaptadorOpenData, AdaptadorOpenFinance
from app.ports.persistencia import FabricaUnidadDeTrabajo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_adaptador_open_finance(request: Request) -> AdaptadorOpenFinance:
    return request.app.state.adaptador_open_finance


def obtener_adaptador_open_data(request: Request) -> AdaptadorOpenData:
    return request.app.state.adaptador_open_data


def obtener_config(request: Request) -> Settings:
    return request.app.state.config
