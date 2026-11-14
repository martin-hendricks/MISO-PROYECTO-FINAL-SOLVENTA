import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.dependencies import obtener_uow
from app.main import crear_app

from .dobles import AlmacenEnMemoria, UnidadDeTrabajoEnMemoria

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")


def token(rol: str = "asesor") -> str:
    payload = {
        "sub": "persona@correo.com",
        "rol": rol,
        "typ": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    return jwt.encode(payload, os.environ["SOLVENTA_TOKEN_SECRET"], algorithm="HS256")


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def uow(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


@pytest.fixture
def client(uow) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    cliente = TestClient(app)
    cliente.headers.update({"Authorization": f"Bearer {token()}"})
    return cliente
