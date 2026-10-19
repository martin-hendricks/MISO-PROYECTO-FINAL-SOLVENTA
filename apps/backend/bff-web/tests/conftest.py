import os

os.environ["SOLVENTA_TOKEN_SECRET"] = "test-secret"

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def token(client: TestClient, rol: str) -> str:
    response = client.post(
        "/sesion/ingreso",
        json={"correo": "persona@solventa.com", "contrasena": "secreto", "rol": rol},
    )
    assert response.status_code == 200
    return response.json()["accessToken"]
