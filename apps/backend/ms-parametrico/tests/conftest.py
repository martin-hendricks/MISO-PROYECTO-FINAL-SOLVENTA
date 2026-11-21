import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.infrastructure.memoria import PublicadorEnMemoria
from app.main import crear_app

CABECERAS = {"X-Telemetria-Cliente": "proveedor-demo", "X-Telemetria-Secreto": "secreto-demo"}


def config_prueba(**extra) -> Settings:
    valores = {
        "msk_bootstrap_brokers": "",
        "TELEMETRIA_CLIENT_ID": "proveedor-demo",
        "TELEMETRIA_CLIENT_SECRET": "secreto-demo",
        **extra,
    }
    return Settings(_env_file=None, **valores)


@pytest.fixture
def publicador() -> PublicadorEnMemoria:
    return PublicadorEnMemoria()


@pytest.fixture
def client(publicador):
    with TestClient(crear_app(config_prueba(), publicador=publicador)) as c:
        yield c


def reporte_vuelo(**extra) -> dict:
    return {
        "reporte_id": "R-1",
        "vuelo": "av234",
        "fecha": "2026-11-20",
        "retraso_minutos": 190,
        "reportado_en": "2026-11-20T14:00:00Z",
        "cobertura": {"umbral": "120", "monto": "180000.00", "poliza_numero": "POL-77310"},
        **extra,
    }


def medicion_clima(**extra) -> dict:
    return {
        "medicion_id": "M-9",
        "estacion": "BOG-01",
        "precipitacion_mm": "85.5",
        "medido_en": "2026-11-20T06:00:00Z",
        "cobertura": {"umbral": "60", "monto": "250000.00"},
        **extra,
    }
