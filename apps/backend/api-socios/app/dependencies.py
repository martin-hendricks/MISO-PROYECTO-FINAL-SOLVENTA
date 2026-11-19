from fastapi import Request

from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.clients.ms_identidad import ClienteMsIdentidad
from app.clients.ms_perfilamiento import ClienteMsPerfilamiento
from app.clients.token_servicio import token_de_socio
from app.seguridad import Socio, SocioDep


def _correlacion(request: Request) -> str | None:
    return getattr(request.state, "correlacion", None)


def _token(request: Request, socio: Socio) -> str:
    return token_de_socio(request.app.state.config.solventa_token_secret, str(socio.socio_id))


def obtener_cliente_cotizacion(request: Request) -> ClienteMsCotizacion:
    return ClienteMsCotizacion(request.app.state.http_ms_cotizacion, _correlacion(request))


def obtener_cliente_identidad(request: Request, socio: SocioDep) -> ClienteMsIdentidad:
    return ClienteMsIdentidad(request.app.state.http_ms_identidad, _correlacion(request), _token(request, socio))


def obtener_cliente_perfilamiento(request: Request, socio: SocioDep) -> ClienteMsPerfilamiento:
    return ClienteMsPerfilamiento(request.app.state.http_ms_perfilamiento, _correlacion(request), _token(request, socio))
