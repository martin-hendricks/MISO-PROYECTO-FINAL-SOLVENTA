from fastapi import Request

from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.precondiciones import VerificadorCobro, VerificadorSuscripcion


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_suscripciones(request: Request) -> VerificadorSuscripcion:
    return request.app.state.suscripciones


def obtener_cobros(request: Request) -> VerificadorCobro:
    return request.app.state.cobros
