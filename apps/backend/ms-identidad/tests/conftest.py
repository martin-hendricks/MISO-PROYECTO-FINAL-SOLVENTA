import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture
def client(uow, kyc) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_verificador_kyc] = lambda: kyc
    return TestClient(app)
