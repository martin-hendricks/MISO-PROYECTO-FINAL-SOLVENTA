from typing import Annotated

from fastapi import Depends, Request

from app.ports.persistencia import FabricaUnidadDeTrabajo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
