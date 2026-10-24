import os
from collections.abc import Callable

os.environ["SOLVENTA_TOKEN_SECRET"] = "test-secret"

import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.clients.ms_pagos import ClienteMsPagos
from app.clients.ms_polizas import ClienteMsPolizas
from app.dependencies import obtener_cliente_cotizacion, obtener_cliente_pagos, obtener_cliente_polizas
from app.main import app


class NucleoSimulado:
    """Doble de un microservicio de núcleo detrás de httpx.MockTransport.

    Mismo patrón que apps/backend/api-socios/tests/conftest.py: registra las
    peticiones recibidas y permite sobrescribir la respuesta de una ruta
    concreta para simular casos de error (404/409/422/caída del servicio).
    """

    def __init__(self, default_status: int = 404, default_body: dict | None = None) -> None:
        self.peticiones: list[httpx.Request] = []
        self.respuestas: dict[tuple[str, str], Callable[[httpx.Request], httpx.Response]] = {}
        self._default_status = default_status
        self._default_body = default_body or {"codigo": "no_encontrado", "mensaje": "No existe"}

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        clave = (request.method, request.url.path)
        if clave in self.respuestas:
            return self.respuestas[clave](request)
        return httpx.Response(self._default_status, json=self._default_body)


@pytest.fixture
def nucleo_cotizacion() -> NucleoSimulado:
    return NucleoSimulado()


@pytest.fixture
def nucleo_pagos() -> NucleoSimulado:
    return NucleoSimulado()


@pytest.fixture
def nucleo_polizas() -> NucleoSimulado:
    return NucleoSimulado()


@pytest.fixture
def client(nucleo_cotizacion, nucleo_pagos, nucleo_polizas) -> TestClient:
    http_cotizacion = httpx.AsyncClient(transport=httpx.MockTransport(nucleo_cotizacion), base_url="http://ms-cotizacion")
    http_pagos = httpx.AsyncClient(transport=httpx.MockTransport(nucleo_pagos), base_url="http://ms-pagos")
    http_polizas = httpx.AsyncClient(transport=httpx.MockTransport(nucleo_polizas), base_url="http://ms-polizas")

    app.dependency_overrides[obtener_cliente_cotizacion] = lambda: ClienteMsCotizacion(http_cotizacion, "corr-test")
    app.dependency_overrides[obtener_cliente_pagos] = lambda: ClienteMsPagos(http_pagos, "corr-test")
    app.dependency_overrides[obtener_cliente_polizas] = lambda: ClienteMsPolizas(http_polizas, "corr-test")
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def token(client: TestClient, rol: str) -> str:
    response = client.post(
        "/sesion/ingreso",
        json={"correo": "persona@solventa.com", "contrasena": "secreto", "rol": rol},
    )
    assert response.status_code == 200
    return response.json()["accessToken"]
