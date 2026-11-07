from fastapi import Request

from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.push import EnviadorPush


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_push(request: Request) -> EnviadorPush:
    return request.app.state.push
