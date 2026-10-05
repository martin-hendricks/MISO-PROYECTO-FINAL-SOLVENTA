from fastapi import Request

from app.clients.ms_ejemplo import ClienteMsEjemplo


def obtener_cliente_ejemplo(request: Request) -> ClienteMsEjemplo:
    return ClienteMsEjemplo(request.app.state.http_ms_ejemplo, getattr(request.state, "correlacion", None))
