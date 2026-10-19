from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.config import Settings
from app.dependencies import obtener_cliente_cotizacion
from app.main import crear_app

PRODUCTO = {
    "producto": "soat-motocicleta",
    "nombre": "SOAT motocicleta",
    "moneda": "COP",
    "coberturas": [
        {"codigo": "gastos_medicos", "nombre": "Gastos médicos", "limite": "800.00", "unidad_limite": "SMLDV"},
        {"codigo": "muerte", "nombre": "Muerte y gastos funerarios", "limite": "750.00", "unidad_limite": "SMLDV"},
    ],
    "datos_riesgo": [
        {"nombre": "cilindraje_cc", "tipo": "rango", "minimo": "50", "maximo": "1800", "valores": None},
        {"nombre": "ciudad_circulacion", "tipo": "valores", "minimo": None, "maximo": None, "valores": ["bogota", "cali"]},
    ],
    "campo_interno_del_nucleo": "no debe llegar al socio",
}


class NucleoSimulado:
    def __init__(self) -> None:
        self.peticiones: list[httpx.Request] = []
        self.respuestas: dict[tuple[str, str], Callable[[httpx.Request], httpx.Response]] = {}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        clave = (request.method, request.url.path)
        if clave in self.respuestas:
            return self.respuestas[clave](request)
        if clave == ("GET", "/v1/productos"):
            return httpx.Response(200, json=[PRODUCTO])
        if clave == ("GET", f"/v1/productos/{PRODUCTO['producto']}"):
            return httpx.Response(200, json=PRODUCTO)
        return httpx.Response(404, json={"codigo": "producto_no_encontrado", "mensaje": "No existe"})


@pytest.fixture
def nucleo() -> NucleoSimulado:
    return NucleoSimulado()


@pytest.fixture
def app(nucleo):
    app = crear_app(Settings())
    http = httpx.AsyncClient(transport=httpx.MockTransport(nucleo), base_url="http://ms-cotizacion")
    app.dependency_overrides[obtener_cliente_cotizacion] = lambda: ClienteMsCotizacion(http, "corr-test")
    return app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)
