import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")

from app.dependencies import obtener_push, obtener_uow
from app.main import crear_app

from .dobles import AlmacenEnMemoria, PushDoble, UnidadDeTrabajoEnMemoria

USUARIO = UUID("11111111-1111-1111-1111-111111111111")
OTRO = UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def uow(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


@pytest.fixture
def push() -> PushDoble:
    return PushDoble()


@pytest.fixture
def app(uow, push):
    aplicacion = crear_app()
    aplicacion.dependency_overrides[obtener_uow] = lambda: uow
    aplicacion.dependency_overrides[obtener_push] = lambda: push
    return aplicacion


@pytest.fixture
def client(app) -> TestClient:
    return _Cliente(app, uid=USUARIO)


@pytest.fixture
def client_otro(app) -> TestClient:
    return _Cliente(app, uid=OTRO)


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
    def __init__(self, app, uid: UUID = USUARIO, rol: str = "cliente") -> None:
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
