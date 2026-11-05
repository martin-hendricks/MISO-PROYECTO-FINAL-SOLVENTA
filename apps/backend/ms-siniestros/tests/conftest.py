import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")

from app.dependencies import obtener_adaptador_desembolso, obtener_uow
from app.infrastructure.pagos import AdaptadorDesembolsoStub
from app.main import crear_app

from .dobles import AlmacenEnMemoria, UnidadDeTrabajoEnMemoria


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def uow(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


@pytest.fixture
def adaptador_desembolso() -> AdaptadorDesembolsoStub:
    return AdaptadorDesembolsoStub()


@pytest.fixture
def client(uow, adaptador_desembolso) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_adaptador_desembolso] = lambda: adaptador_desembolso
    return _Cliente(app)


def _token() -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": "operador@solventa.co",
            "uid": "00000000-0000-0000-0000-000000000001",
            "rol": "operador",
            "typ": "access",
            "exp": now + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )


class _Cliente(TestClient):
    def request(self, method, url, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("Authorization", f"Bearer {_token()}")
        kwargs["headers"] = headers
        return super().request(method, url, **kwargs)
