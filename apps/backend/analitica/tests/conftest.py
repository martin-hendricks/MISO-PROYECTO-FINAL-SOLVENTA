import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")

from app.dependencies import obtener_uow
from app.main import crear_app

from .dobles import AlmacenEnMemoria, UnidadDeTrabajoEnMemoria

OPERADOR = UUID("11111111-1111-1111-1111-111111111111")
CLIENTE = UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def uow(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


@pytest.fixture
def app(uow):
    aplicacion = crear_app()
    aplicacion.dependency_overrides[obtener_uow] = lambda: uow
    return aplicacion


@pytest.fixture
def client(app) -> TestClient:
    return _Cliente(app, uid=OPERADOR, rol="operador")


@pytest.fixture
def client_cliente(app) -> TestClient:
    return _Cliente(app, uid=CLIENTE, rol="cliente")


def _token(uid: UUID, rol: str) -> str:
    ahora = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": f"{uid}@solventa.co",
            "uid": str(uid),
            "rol": rol,
            "typ": "access",
            "exp": ahora + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )


class _Cliente(TestClient):
    def __init__(self, app, uid: UUID, rol: str) -> None:
        super().__init__(app)
        self._uid = uid
        self._rol = rol

    def request(self, method, url, **kwargs):
        sin_token = kwargs.pop("sin_token", False)
        headers = dict(kwargs.pop("headers", None) or {})
        if not sin_token:
            headers.setdefault("Authorization", f"Bearer {_token(self._uid, self._rol)}")
        kwargs["headers"] = headers
        return super().request(method, url, **kwargs)
