from fastapi import Request

from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.precondiciones import VerificadorCobro, VerificadorSuscripcion


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_uow_lectura(request: Request) -> FabricaUnidadDeTrabajo:
    """EC-LAT-10: fábrica de UoW contra el motor de lectura (réplica activa de
    DBPolizas). Úsala en los endpoints que solo consultan."""
    return request.app.state.fabrica_uow_lectura


def obtener_suscripciones(request: Request) -> VerificadorSuscripcion:
    return request.app.state.suscripciones


def obtener_cobros(request: Request) -> VerificadorCobro:
    return request.app.state.cobros
