import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")

from app.config import Settings
from app.dependencies import (
    obtener_adaptador_perfil_riesgo,
    obtener_catalogo,
    obtener_config,
    obtener_consentimientos,
    obtener_suscripciones,
    obtener_uow,
)
from app.infrastructure.adaptador_perfil_stub import AdaptadorPerfilRiesgoStub
from app.main import crear_app

from .dobles import (
    AlmacenEnMemoria,
    CatalogoEnMemoria,
    ConsentimientosFalsos,
    SuscripcionesFalsas,
    UnidadDeTrabajoEnMemoria,
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
def catalogo() -> CatalogoEnMemoria:
    return CatalogoEnMemoria()


@pytest.fixture
def adaptador_riesgo():
    return AdaptadorPerfilRiesgoStub(latencia_ms=1, factor_fijo=Decimal("1.0"))


@pytest.fixture
def config():
    return Settings()


@pytest.fixture
def suscripciones() -> SuscripcionesFalsas:
    return SuscripcionesFalsas()


@pytest.fixture
def consentimientos() -> ConsentimientosFalsos:
    return ConsentimientosFalsos()


@pytest.fixture
def client(uow, catalogo, adaptador_riesgo, config, suscripciones, consentimientos) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    app.dependency_overrides[obtener_catalogo] = lambda: catalogo
    app.dependency_overrides[obtener_adaptador_perfil_riesgo] = lambda: adaptador_riesgo
    app.dependency_overrides[obtener_config] = lambda: config
    app.dependency_overrides[obtener_suscripciones] = lambda: suscripciones
    app.dependency_overrides[obtener_consentimientos] = lambda: consentimientos
    return _cliente(app)


def _token() -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": "operador@solventa.co",
            "uid": "00000000-0000-0000-0000-000000000001",
            "rol": "operador",
            "typ": "access",
            "exp": now + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )


class _Cliente(TestClient):
    def request(self, method, url, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("Authorization", f"Bearer {_token()}")
        kwargs["headers"] = headers
        return super().request(method, url, **kwargs)


def _cliente(app) -> TestClient:
    return _Cliente(app)
