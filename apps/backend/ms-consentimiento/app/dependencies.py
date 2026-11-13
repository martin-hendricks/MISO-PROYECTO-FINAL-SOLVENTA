from fastapi import Request

from app.ports.persistencia import FabricaUnidadDeTrabajo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow
