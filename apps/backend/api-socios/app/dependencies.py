from fastapi import Request

from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.clients.ms_identidad import ClienteMsIdentidad
from app.clients.ms_perfilamiento import ClienteMsPerfilamiento
from app.clients.token_servicio import token_de_socio


def _correlacion(request: Request) -> str | None:
    return getattr(request.state, "correlacion", None)


def obtener_cliente_cotizacion(request: Request) -> ClienteMsCotizacion:
    return ClienteMsCotizacion(request.app.state.http_ms_cotizacion, _correlacion(request))


def obtener_cliente_identidad(request: Request) -> ClienteMsIdentidad:
    config = request.app.state.config
    token = token_de_socio(config.solventa_token_secret, config.socio_servicio_uid)
    return ClienteMsIdentidad(request.app.state.http_ms_identidad, _correlacion(request), token)


def obtener_cliente_perfilamiento(request: Request) -> ClienteMsPerfilamiento:
    return ClienteMsPerfilamiento(request.app.state.http_ms_perfilamiento, _correlacion(request))
