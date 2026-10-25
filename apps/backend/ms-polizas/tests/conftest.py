import pytest
from fastapi.testclient import TestClient

from app.dependencies import (
    obtener_cobros,
    obtener_firma,
    obtener_suscripciones,
    obtener_uow,
    obtener_uow_lectura,
)
from app.main import crear_app

from .dobles import (
    AlmacenEnMemoria,
    CobrosFalsos,
    FirmaFalsa,
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
def firma() -> FirmaFalsa:
    return FirmaFalsa()


@pytest.fixture
def client(uow, suscripciones, cobros, firma) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    # En el doble de test no hay réplica real de lectura separada: la misma
    # UoW en memoria sirve ambos roles (ver obtener_uow_lectura en producción,
    # que sí usa un motor SQLAlchemy distinto).
    app.dependency_overrides[obtener_uow_lectura] = lambda: uow
    app.dependency_overrides[obtener_suscripciones] = lambda: suscripciones
    app.dependency_overrides[obtener_cobros] = lambda: cobros
    app.dependency_overrides[obtener_firma] = lambda: firma
    return TestClient(app)
