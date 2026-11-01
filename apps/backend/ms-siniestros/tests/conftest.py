import pytest
from fastapi.testclient import TestClient

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
    return TestClient(app)
