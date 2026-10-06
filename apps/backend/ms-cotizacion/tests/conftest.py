from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.application.casos_uso import Colaboradores
from app.dependencies import obtener_colaboradores
from app.infrastructure.catalogo_memoria import CatalogoEnMemoria
from app.infrastructure.memoria import RepositorioCotizacionesEnMemoria
from app.main import crear_app

from .dobles import FactorEspia, PrimaEspia, RelojFijo

VIGENCIA = timedelta(hours=24)
DATOS_VALIDOS = {"valorDispositivo": 2_400_000, "marca": "Pixel", "masDe12Meses": False}


@pytest.fixture
def reloj() -> RelojFijo:
    return RelojFijo()


@pytest.fixture
def prima() -> PrimaEspia:
    return PrimaEspia()


@pytest.fixture
def factor() -> FactorEspia:
    return FactorEspia()


@pytest.fixture
def repositorio() -> RepositorioCotizacionesEnMemoria:
    return RepositorioCotizacionesEnMemoria()


@pytest.fixture
def deps(reloj, prima, factor, repositorio) -> Colaboradores:
    return Colaboradores(
        catalogo=CatalogoEnMemoria(),
        calculadora_prima=prima,
        factor_riesgo=factor,
        cotizaciones=repositorio,
        reloj=reloj,
        vigencia_oferta=VIGENCIA,
    )


@pytest.fixture
def client(deps) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_colaboradores] = lambda: deps
    return TestClient(app)
