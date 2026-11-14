import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.dependencies import (
    obtener_adaptador_open_data,
    obtener_adaptador_open_finance,
    obtener_cache_fuentes,
    obtener_config,
    obtener_uow,
)
from app.infrastructure.cache_fuentes import CacheEnMemoria
from app.domain.precio import ANTIGUEDAD_DOCUMENTO, NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO, ZONA_RIESGO
from app.main import crear_app

from .dobles import AdaptadorConfigurable, AlmacenEnMemoria, UnidadDeTrabajoEnMemoria

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")


def token(rol: str = "asesor") -> str:
    payload = {
        "sub": "persona@correo.com",
        "rol": rol,
        "typ": "access",
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    return jwt.encode(payload, os.environ["SOLVENTA_TOKEN_SECRET"], algorithm="HS256")


@pytest.fixture
def almacen() -> AlmacenEnMemoria:
    return AlmacenEnMemoria()


@pytest.fixture
def uow(almacen):
    return lambda: UnidadDeTrabajoEnMemoria(almacen)


@pytest.fixture
def config() -> Settings:
    return Settings(
        database_url="postgresql+asyncpg://postgres:postgres@localhost:5432/solventa",
        timeout_open_finance_ms=50,
        timeout_open_data_ms=50,
    )


@pytest.fixture
def adaptador_open_finance() -> AdaptadorConfigurable:
    return AdaptadorConfigurable(
        {NIVEL_INGRESOS_ESTIMADO: Decimal("0.700"), SCORE_COMPORTAMIENTO: Decimal("0.800")}
    )


@pytest.fixture
def adaptador_open_data() -> AdaptadorConfigurable:
    return AdaptadorConfigurable({ZONA_RIESGO: Decimal("0.300"), ANTIGUEDAD_DOCUMENTO: Decimal("0.600")})


@pytest.fixture
def client(uow, config, adaptador_open_finance, adaptador_open_data) -> TestClient:
    app = crear_app(config)
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_config] = lambda: config
    app.dependency_overrides[obtener_adaptador_open_finance] = lambda: adaptador_open_finance
    app.dependency_overrides[obtener_adaptador_open_data] = lambda: adaptador_open_data
    app.dependency_overrides[obtener_cache_fuentes] = lambda: CacheEnMemoria()
    cliente = TestClient(app)
    cliente.headers.update({"Authorization": f"Bearer {token()}"})
    return cliente
