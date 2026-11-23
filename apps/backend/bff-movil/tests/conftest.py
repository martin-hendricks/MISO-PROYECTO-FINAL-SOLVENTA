import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ["SOLVENTA_TOKEN_SECRET"] = "test-secret"

from app.main import app

UID = "11111111-1111-1111-1111-111111111111"


class IdentidadDePrueba:
    """Cubre el ingreso cuando el test no instala su propio doble del núcleo."""

    def autenticar(self, *, correo, contrasena):
        return {"usuario_id": UID, "email": correo.strip().lower(), "estado": "ACTIVO"}


@pytest.fixture(autouse=True)
def identidad_de_prueba():
    anterior = app.state.nucleo
    if type(anterior).__name__ == "ClienteNucleo":
        app.state.nucleo = IdentidadDePrueba()
    yield
    app.state.nucleo = anterior


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def customer_token(client: TestClient) -> str:
    response = client.post(
        "/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    )
    assert response.status_code == 200
    return response.json()["accessToken"]


def desk_token(rol: str) -> str:
    return jwt.encode(
        {
            "sub": "desk@solventa.com",
            "rol": rol,
            "typ": "access",
            "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )
