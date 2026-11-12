from fastapi import Request

from app.config import Settings
from app.ports.evidencias import AlmacenEvidencias
from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import FabricaUnidadDeTrabajo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_adaptador_desembolso(request: Request) -> AdaptadorDesembolso:
    return request.app.state.adaptador_desembolso


def obtener_almacen_evidencias(request: Request) -> AlmacenEvidencias:
    return request.app.state.almacen_evidencias


def obtener_config(request: Request) -> Settings:
    return request.app.state.config
