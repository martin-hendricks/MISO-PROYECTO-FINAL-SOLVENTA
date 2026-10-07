from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import obtener_adaptador_perfil_riesgo, obtener_catalogo, obtener_config, obtener_uow
from app.infrastructure.adaptador_perfil_stub import AdaptadorPerfilRiesgoStub
from app.main import crear_app

from .dobles import (
    AlmacenEnMemoria,
    UnidadDeTrabajoEnMemoria,
    catalogo_de_prueba,
    regla_rating_soat_motocicleta,
)


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
def catalogo():
    return catalogo_de_prueba()


@pytest.fixture
def adaptador_riesgo():
    return AdaptadorPerfilRiesgoStub(latencia_ms=1, factor_fijo=Decimal("1.0"))


@pytest.fixture
def config():
    return Settings()


@pytest.fixture
def client(uow, catalogo, adaptador_riesgo, config) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_catalogo] = lambda: catalogo
    app.dependency_overrides[obtener_adaptador_perfil_riesgo] = lambda: adaptador_riesgo
    app.dependency_overrides[obtener_config] = lambda: config
    return TestClient(app)
