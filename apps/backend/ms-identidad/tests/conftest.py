import os
from datetime import datetime, timedelta, timezone
import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")

from app.dependencies import (
    obtener_cliente_consentimiento,
    obtener_cliente_perfilamiento,
    obtener_uow,
    obtener_verificador_kyc,
)
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


class _ConsultaConsentimientoDoble:
    """Doble de ConsultaConsentimiento (ms-consentimiento) para tests de API:
    por defecto "sin habeas data vigente", igual que respondería un 404 real."""

    def __init__(self, vigente: bool = False) -> None:
        self.vigente_valor = vigente

    async def vigente(self, cliente_id: str) -> bool:
        return self.vigente_valor


class _ConsultaPerfilamientoDoble:
    """Doble de ConsultaPerfilamiento (ms-perfilamiento) para tests de API:
    por defecto "sin originación pendiente"."""

    def __init__(self, pendiente: bool = False) -> None:
        self.pendiente_valor = pendiente

    async def tiene_originacion_pendiente(self, cliente_id: str) -> bool:
        return self.pendiente_valor


@pytest.fixture
def consentimiento() -> _ConsultaConsentimientoDoble:
    return _ConsultaConsentimientoDoble()


@pytest.fixture
def perfilamiento() -> _ConsultaPerfilamientoDoble:
    return _ConsultaPerfilamientoDoble()


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
def client(uow, kyc, consentimiento, perfilamiento) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_verificador_kyc] = lambda: kyc
    app.dependency_overrides[obtener_cliente_consentimiento] = lambda: consentimiento
    app.dependency_overrides[obtener_cliente_perfilamiento] = lambda: perfilamiento
    return ClienteConToken(app)
