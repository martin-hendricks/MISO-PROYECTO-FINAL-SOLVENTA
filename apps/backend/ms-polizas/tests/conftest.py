import pytest
from fastapi.testclient import TestClient

from app.dependencies import obtener_cobros, obtener_suscripciones, obtener_uow
from app.main import crear_app

from .dobles import (
    AlmacenEnMemoria,
    CobrosFalsos,
    SuscripcionesFalsas,
    UnidadDeTrabajoEnMemoria,
)


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def uow(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


@pytest.fixture
def suscripciones() -> SuscripcionesFalsas:
    return SuscripcionesFalsas()


@pytest.fixture
def cobros() -> CobrosFalsos:
    return CobrosFalsos()


@pytest.fixture
def client(uow, suscripciones, cobros) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_suscripciones] = lambda: suscripciones
    app.dependency_overrides[obtener_cobros] = lambda: cobros
    return TestClient(app)
