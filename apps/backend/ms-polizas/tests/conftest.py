import os
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SOLVENTA_TOKEN_SECRET", "test-secret")

from app.dependencies import (
    obtener_cobros,
    obtener_firma,
    obtener_reportes,
    obtener_suscripciones,
    obtener_uow,
    obtener_uow_lectura,
)
from app.main import crear_app

from .dobles import (
    AlmacenEnMemoria,
    CobrosFalsos,
    FirmaFalsa,
    ReportesFalsos,
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
def reportes() -> ReportesFalsos:
    return ReportesFalsos()


@pytest.fixture
def client(uow, suscripciones, cobros, firma, reportes) -> TestClient:
    app = crear_app()
    app.dependency_overrides[obtener_uow] = lambda: uow
    # En el doble de test no hay réplica real de lectura separada: la misma
    # UoW en memoria sirve ambos roles (ver obtener_uow_lectura en producción,
    # que sí usa un motor SQLAlchemy distinto).
    app.dependency_overrides[obtener_uow_lectura] = lambda: uow
    app.dependency_overrides[obtener_suscripciones] = lambda: suscripciones
    app.dependency_overrides[obtener_cobros] = lambda: cobros
    app.dependency_overrides[obtener_firma] = lambda: firma
    app.dependency_overrides[obtener_reportes] = lambda: reportes
    return _Cliente(app)


def _token(rol: str = "operador", uid: str | None = None) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": f"{rol}@solventa.co",
            "uid": uid or "00000000-0000-0000-0000-000000000001",
            "rol": rol,
            "typ": "access",
            "exp": now + timedelta(minutes=5),
        },
        "test-secret",
        algorithm="HS256",
    )


class _Cliente(TestClient):
    def __init__(self, app, rol: str = "operador", uid: str | None = None, **kwargs) -> None:
        super().__init__(app, **kwargs)
        self._rol = rol
        self._uid = uid

    def request(self, method, url, **kwargs):
        headers = dict(kwargs.pop("headers", None) or {})
        headers.setdefault("Authorization", f"Bearer {_token(self._rol, self._uid)}")
        kwargs["headers"] = headers
        return super().request(method, url, **kwargs)

    def como(self, rol: str, uid: str | None = None) -> "_Cliente":
        """Mismo cliente, con un token de otro rol -- para tests de
        autorización (HU-62/HU-63 exigen rol operador en las rutas de
        reportes; HU-119 exige que 'alcance()' filtre al cliente a lo suyo)."""
        return _Cliente(self.app, rol=rol, uid=uid)
