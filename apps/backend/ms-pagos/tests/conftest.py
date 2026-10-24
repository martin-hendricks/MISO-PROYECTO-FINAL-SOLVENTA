import pytest
from fastapi.testclient import TestClient

from app.dependencies import obtener_pasarela, obtener_suscripciones, obtener_uow
from app.infrastructure.externos import PasarelaStub
from app.main import crear_app

from .dobles import (
    AlmacenEnMemoria,
    PasarelaEspia,
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
def pasarela() -> PasarelaEspia:
    return PasarelaEspia(PasarelaStub())


@pytest.fixture
def client(uow, suscripciones, pasarela) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_suscripciones] = lambda: suscripciones
    app.dependency_overrides[obtener_pasarela] = lambda: pasarela
    return TestClient(app)
