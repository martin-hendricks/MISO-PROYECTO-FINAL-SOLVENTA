import pytest
from fastapi.testclient import TestClient

from app.dependencies import obtener_catalogo, obtener_uow
from app.main import crear_app

from .dobles import AlmacenEnMemoria, CatalogoEnMemoria, UnidadDeTrabajoEnMemoria, regla_rating_soat_motocicleta


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    almacen = AlmacenEnMemoria()
    regla = regla_rating_soat_motocicleta()
    almacen.reglas_rating[regla.id] = regla
    return almacen


@pytest.fixture
def uow(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


@pytest.fixture
def catalogo() -> CatalogoEnMemoria:
    return CatalogoEnMemoria()


@pytest.fixture
def client(uow, catalogo) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_catalogo] = lambda: catalogo
    return TestClient(app)
