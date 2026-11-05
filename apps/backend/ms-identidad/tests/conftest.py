import os
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")

from app.dependencies import obtener_uow, obtener_verificador_kyc
from app.infrastructure.kyc import VerificadorKYCStub
from app.main import crear_app

from .dobles import AlmacenEnMemoria, UnidadDeTrabajoEnMemoria


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def uow(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


@pytest.fixture
def kyc() -> VerificadorKYCStub:
    return VerificadorKYCStub()


def token_de(uid: str, rol: str = "operador") -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {"sub": "prueba@solventa.co", "uid": uid, "rol": rol, "typ": "access", "exp": now + timedelta(minutes=5)},
        "test-secret",
        algorithm="HS256",
    )


class ClienteConToken(TestClient):
    def request(self, method, url, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        if "Authorization" not in headers:
            headers["Authorization"] = f"Bearer {token_de('00000000-0000-0000-0000-000000000001')}"
        kwargs["headers"] = headers
        return super().request(method, url, **kwargs)


@pytest.fixture
def client(uow, kyc) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_verificador_kyc] = lambda: kyc
    return ClienteConToken(app)
