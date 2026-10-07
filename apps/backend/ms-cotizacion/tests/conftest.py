import pytest
from fastapi.testclient import TestClient

from app.dependencies import obtener_catalogo, obtener_uow
from app.main import crear_app

from .dobles import AlmacenEnMemoria, UnidadDeTrabajoEnMemoria, catalogo_de_prueba


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def uow(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


@pytest.fixture
def catalogo():
    return catalogo_de_prueba()


@pytest.fixture
def client(uow, catalogo) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_catalogo] = lambda: catalogo
    return TestClient(app)
