"""Cubre crear_app()/lifespan: arranque y apagado sin broker real
configurado (camino feliz de tests/entornos sin bus), y con broker
configurado pero el consumidor MSK mockeado (sin conexión real)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import crear_app


def test_lifespan_sin_brokers_no_arranca_consumidor():
    config = Settings(msk_bootstrap_brokers="")
    app = crear_app(config)

    with patch("app.main.ConsumidorMSK") as ConsumidorMock:
        with TestClient(app) as client:
            respuesta = client.get("/metrics")
            assert respuesta.status_code == 200

        ConsumidorMock.assert_not_called()


def test_lifespan_con_brokers_arranca_y_detiene_el_consumidor():
    config = Settings(msk_bootstrap_brokers="b-1.solventa.kafka:9098")
    app = crear_app(config)

    consumidor_falso = AsyncMock()
    with patch("app.main.ConsumidorMSK", return_value=consumidor_falso) as ConsumidorMock:
        with TestClient(app) as client:
            respuesta = client.get("/metrics")
            assert respuesta.status_code == 200

        ConsumidorMock.assert_called_once()
        consumidor_falso.iniciar.assert_awaited_once()
        consumidor_falso.detener.assert_awaited_once()
