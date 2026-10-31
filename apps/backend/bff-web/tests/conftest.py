import os
from collections.abc import Callable

os.environ["SOLVENTA_TOKEN_SECRET"] = "test-secret"

import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.clients.ms_identidad import ClienteMsIdentidad
from app.clients.ms_pagos import ClienteMsPagos
from app.clients.ms_perfilamiento import ClienteMsPerfilamiento
from app.clients.ms_polizas import ClienteMsPolizas
from app.clients.ms_siniestros import ClienteMsSiniestros
from app.clients.ms_suscripcion import ClienteMsSuscripcion
from app.dependencies import (
    obtener_cliente_cotizacion,
    obtener_cliente_identidad,
    obtener_cliente_pagos,
    obtener_cliente_perfilamiento,
    obtener_cliente_polizas,
    obtener_cliente_siniestros,
    obtener_cliente_suscripcion,
)
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
def nucleo_perfilamiento() -> NucleoSimulado:
    return NucleoSimulado()


@pytest.fixture
def nucleo_siniestros() -> NucleoSimulado:
    # A diferencia de un recurso puntual (ej. GET /v1/polizas/{id}), listar
    # siniestros sin ninguno registrado es una respuesta vigente (lista
    # vacía), no un 404 -- por eso este doble fija ese default en vez de usar
    # el genérico 404 de NucleoSimulado, igual que haría ms-siniestros real.
    doble = NucleoSimulado()
    doble.respuestas[("GET", "/v1/siniestros")] = lambda _: httpx.Response(200, json=[])
    return doble


@pytest.fixture
def nucleo_suscripcion() -> NucleoSimulado:
    return NucleoSimulado()


@pytest.fixture
def nucleo_identidad() -> NucleoSimulado:
    # A diferencia del default generico 404 de NucleoSimulado, alta y
    # autenticacion exitosas son el caso feliz mas comun en los tests de
    # registro.py/sesion.py -- cada test que necesite un rechazo (409/401)
    # sobrescribe la respuesta explicitamente, igual que con los demas.
    doble = NucleoSimulado()
    doble.respuestas[("POST", "/v1/usuarios")] = lambda request: httpx.Response(
        201,
        json={
            "usuario_id": "11111111-1111-1111-1111-111111111111",
            "tipo_documento": "CC",
            "numero_documento": "0",
            "email": "sin-email@solventa.com",
            "estado": "ACTIVO",
        },
    )
    doble.respuestas[("POST", "/v1/usuarios/autenticacion")] = lambda request: httpx.Response(
        200,
        json={
            "usuario_id": "11111111-1111-1111-1111-111111111111",
            "tipo_documento": "CC",
            "numero_documento": "0",
            "email": "sin-email@solventa.com",
            "estado": "ACTIVO",
        },
    )
    return doble


@pytest.fixture
def client(
    nucleo_cotizacion,
    nucleo_pagos,
    nucleo_polizas,
    nucleo_perfilamiento,
    nucleo_siniestros,
    nucleo_suscripcion,
    nucleo_identidad,
) -> TestClient:
    http_cotizacion = httpx.AsyncClient(transport=httpx.MockTransport(nucleo_cotizacion), base_url="http://ms-cotizacion")
    http_pagos = httpx.AsyncClient(transport=httpx.MockTransport(nucleo_pagos), base_url="http://ms-pagos")
    http_polizas = httpx.AsyncClient(transport=httpx.MockTransport(nucleo_polizas), base_url="http://ms-polizas")
    http_perfilamiento = httpx.AsyncClient(
        transport=httpx.MockTransport(nucleo_perfilamiento), base_url="http://ms-perfilamiento"
    )
    http_siniestros = httpx.AsyncClient(
        transport=httpx.MockTransport(nucleo_siniestros), base_url="http://ms-siniestros"
    )
    http_suscripcion = httpx.AsyncClient(
        transport=httpx.MockTransport(nucleo_suscripcion), base_url="http://ms-suscripcion"
    )
    http_identidad = httpx.AsyncClient(
        transport=httpx.MockTransport(nucleo_identidad), base_url="http://ms-identidad"
    )

    app.dependency_overrides[obtener_cliente_cotizacion] = lambda: ClienteMsCotizacion(http_cotizacion, "corr-test")
    app.dependency_overrides[obtener_cliente_pagos] = lambda: ClienteMsPagos(http_pagos, "corr-test")
    app.dependency_overrides[obtener_cliente_polizas] = lambda: ClienteMsPolizas(http_polizas, "corr-test")
    app.dependency_overrides[obtener_cliente_perfilamiento] = lambda: ClienteMsPerfilamiento(
        http_perfilamiento, "corr-test"
    )
    app.dependency_overrides[obtener_cliente_siniestros] = lambda: ClienteMsSiniestros(http_siniestros, "corr-test")
    app.dependency_overrides[obtener_cliente_suscripcion] = lambda: ClienteMsSuscripcion(
        http_suscripcion, "corr-test"
    )
    app.dependency_overrides[obtener_cliente_identidad] = lambda: ClienteMsIdentidad(http_identidad, "corr-test")
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def token(client: TestClient, rol: str) -> str:
    # El dominio del correo debe ser consistente con el rol pedido (ver
    # routers/sesion.py: una cuenta no corporativa no puede entrar pidiendo
    # rol asesor/operador, y viceversa) -- antes este fixture usaba el mismo
    # correo @solventa.com para cualquier rol, lo que ahora el propio BFF
    # rechazaría para rol="cliente".
    correo = "persona@solventa.com" if rol in ("asesor", "operador") else "persona@correo.com"
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": correo, "contrasena": "secreto", "rol": rol},
    )
    assert response.status_code == 200
    return response.json()["accessToken"]
