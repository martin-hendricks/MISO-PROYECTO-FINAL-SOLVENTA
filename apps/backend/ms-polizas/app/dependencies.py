from fastapi import Request

from app.ports.firma import FirmaElectronica
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.precondiciones import VerificadorCobro, VerificadorSuscripcion
from app.ports.reportes import GeneradorReportes


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


def obtener_firma(request: Request) -> FirmaElectronica:
    return request.app.state.firma


def obtener_reportes(request: Request) -> GeneradorReportes:
    return request.app.state.reportes
