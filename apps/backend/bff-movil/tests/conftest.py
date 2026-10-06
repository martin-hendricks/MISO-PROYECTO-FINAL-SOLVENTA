import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ["SOLVENTA_TOKEN_SECRET"] = "test-secret"

from app.main import app


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
