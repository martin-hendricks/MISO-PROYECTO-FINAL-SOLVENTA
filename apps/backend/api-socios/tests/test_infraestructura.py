from types import SimpleNamespace

import httpx
from fastapi.testclient import TestClient

from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.config import Settings
from app.dependencies import obtener_cliente_cotizacion
from app.main import crear_app


def test_al_arrancar_crea_el_cliente_http_hacia_ms_cotizacion():
    app = crear_app(Settings(ms_cotizacion_url="http://ms-cotizacion:8000"))

    with TestClient(app):
        assert str(app.state.http_ms_cotizacion.base_url) == "http://ms-cotizacion:8000"


def test_dependencia_propaga_la_correlacion():
    http = httpx.AsyncClient()
    request = SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(http_ms_cotizacion=http)),
        state=SimpleNamespace(correlacion="c-1"),
    )

    cliente = obtener_cliente_cotizacion(request)

    assert isinstance(cliente, ClienteMsCotizacion)
    assert cliente._cabeceras == {"X-Correlation-Id": "c-1"}


def test_rechazo_sin_cuerpo_json_usa_codigo_generico(client, nucleo):
    nucleo.respuestas[("GET", "/v1/productos/soat-motocicleta")] = lambda _: httpx.Response(422, text="no json")

    respuesta = client.get("/v1/catalogo/soat-motocicleta")

    assert respuesta.status_code == 422
    assert respuesta.json() == {"codigo": "rechazado", "mensaje": "Operación rechazada"}


def test_health_metrics_y_correlacion(client):
    salud = client.get("/health", headers={"X-Correlation-Id": "c-123"})

    assert salud.json() == {"status": "ok"}
    assert salud.headers["X-Correlation-Id"] == "c-123"
    assert "http_request_duration_seconds" in client.get("/metrics").text
