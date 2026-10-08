from fastapi import Request

from app.clients.ms_cotizacion import ClienteMsCotizacion


def obtener_cliente_cotizacion(request: Request) -> ClienteMsCotizacion:
    return ClienteMsCotizacion(request.app.state.http_ms_cotizacion, getattr(request.state, "correlacion", None))
