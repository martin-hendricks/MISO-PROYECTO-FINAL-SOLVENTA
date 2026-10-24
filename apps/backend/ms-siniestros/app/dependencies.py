from fastapi import Request

from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import FabricaUnidadDeTrabajo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_adaptador_desembolso(request: Request) -> AdaptadorDesembolso:
    return request.app.state.adaptador_desembolso
