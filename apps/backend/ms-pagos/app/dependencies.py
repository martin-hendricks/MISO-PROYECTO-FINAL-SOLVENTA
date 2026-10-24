from fastapi import Request

from app.ports.externos import PasarelaPagos, VerificadorSuscripcion
from app.ports.persistencia import FabricaUnidadDeTrabajo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_suscripciones(request: Request) -> VerificadorSuscripcion:
    return request.app.state.suscripciones


def obtener_pasarela(request: Request) -> PasarelaPagos:
    return request.app.state.pasarela
