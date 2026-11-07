import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")

from app.dependencies import obtener_adaptador_desembolso, obtener_almacen_evidencias, obtener_uow
from app.infrastructure.evidencias import AlmacenEvidenciasEnMemoria
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
def almacen_evidencias() -> AlmacenEvidenciasEnMemoria:
    return AlmacenEvidenciasEnMemoria()


@pytest.fixture
def client(uow, adaptador_desembolso, almacen_evidencias) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_adaptador_desembolso] = lambda: adaptador_desembolso
    app.dependency_overrides[obtener_almacen_evidencias] = lambda: almacen_evidencias
    return _Cliente(app)


def _token(
    rol: str = "operador",
    uid: str = "00000000-0000-0000-0000-000000000001",
    sub: str = "operador@solventa.co",
) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": sub, "uid": uid, "rol": rol, "typ": "access", "exp": now + timedelta(minutes=5)},
        "test-secret",
        algorithm="HS256",
    )


def cabecera(rol: str = "operador", uid=None, sub: str = "") -> dict:
    """Authorization de un llamante concreto (por defecto el cliente de pruebas es operador)."""
    uid = str(uid or "00000000-0000-0000-0000-000000000001")
    return {"Authorization": f"Bearer {_token(rol, uid, sub or f'{rol}@solventa.co')}"}


class _Cliente(TestClient):
    def request(self, method, url, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("Authorization", f"Bearer {_token()}")
        kwargs["headers"] = headers
        return super().request(method, url, **kwargs)
