from collections.abc import Callable

import httpx
import pytest
from fastapi.testclient import TestClient

from app.clients.ms_ejemplo import ClienteMsEjemplo
from app.config import Settings
from app.dependencies import obtener_cliente_ejemplo
from app.main import crear_app
from solventa_seguridad.pruebas import EmisorDePrueba

EMISOR = EmisorDePrueba()

EJEMPLO = {
    "id": "0b6f6c2e-6a43-4a43-9b0e-1f7c2a0d4c11",
    "referencia": "REF-1",
    "monto": "100.00",
    "estado": "registrado",
    "creado_en": "2026-10-04T12:00:00Z",
    "campo_interno_del_nucleo": "no debe llegar al canal",
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
        if clave == ("GET", "/v1/ejemplos"):
            return httpx.Response(200, json=[EJEMPLO])
        if clave == ("GET", "/v1/ejemplos/indicadores"):
            return httpx.Response(200, json={"total": 1, "monto_total": "100.00"})
        if clave == ("POST", "/v1/ejemplos"):
            return httpx.Response(201, json=EJEMPLO)
        if request.method == "GET" and request.url.path == f"/v1/ejemplos/{EJEMPLO['id']}":
            return httpx.Response(200, json=EJEMPLO)
        if request.url.path.endswith("/aprobacion"):
            return httpx.Response(200, json={**EJEMPLO, "estado": "aprobado"})
        return httpx.Response(404, json={"codigo": "no_encontrado", "mensaje": "No existe"})


@pytest.fixture
def nucleo() -> NucleoSimulado:
    return NucleoSimulado()


@pytest.fixture
def app(nucleo):
    app = crear_app(Settings(jwt_public_key=EMISOR.llave_publica_pem, timeout_opcional_s=0.2))
    http = httpx.AsyncClient(transport=httpx.MockTransport(nucleo), base_url="http://ms-ejemplo")
    app.dependency_overrides[obtener_cliente_ejemplo] = lambda: ClienteMsEjemplo(http, "corr-test")
    return app


@pytest.fixture
def client(app) -> TestClient:
    return TestClient(app)


def auth(rol: str = "cliente", sujeto: str = "USR-1") -> dict[str, str]:
    return {"Authorization": f"Bearer {EMISOR.emitir(sujeto, rol)}"}
