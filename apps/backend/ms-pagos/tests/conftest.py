import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.dependencies import obtener_pasarela, obtener_suscripciones, obtener_uow
from app.infrastructure.externos import PasarelaStub
from app.main import crear_app

from .dobles import (
    AlmacenEnMemoria,
    PasarelaEspia,
    SuscripcionesFalsas,
    UnidadDeTrabajoEnMemoria,
)

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")


def token(rol: str = "asesor") -> str:
    payload = {
        "sub": "persona@correo.com",
        "rol": rol,
        "uid": "11111111-1111-1111-1111-111111111111",
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
def suscripciones() -> SuscripcionesFalsas:
    return SuscripcionesFalsas()


@pytest.fixture
def pasarela() -> PasarelaEspia:
    return PasarelaEspia(PasarelaStub())


@pytest.fixture
def client(uow, suscripciones, pasarela) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_suscripciones] = lambda: suscripciones
    app.dependency_overrides[obtener_pasarela] = lambda: pasarela
    cliente = TestClient(app)
    cliente.headers.update({"Authorization": f"Bearer {token()}"})
    return cliente
