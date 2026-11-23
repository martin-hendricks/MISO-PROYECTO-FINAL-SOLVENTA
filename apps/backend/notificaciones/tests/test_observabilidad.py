"""Cubre los endpoints de observabilidad que no requieren una base real:
health/live, health (alias), metrics, y las dos ramas 503 de health/ready
(sin motor configurado, y con motor pero la conexión falla). La rama feliz
de health/ready (SELECT 1 contra una base real) no se cubre aquí -- queda
fuera del alcance de un test unitario sin Postgres real."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.observabilidad import instrumentar


def _app_sin_lifespan() -> FastAPI:
    app = FastAPI()
    instrumentar(app)
    return app


def test_health_ready_sin_motor_configurado_devuelve_503():
    client = TestClient(_app_sin_lifespan())

    respuesta = client.get("/health/ready")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable"}


def test_health_ready_con_motor_que_falla_al_conectar_devuelve_503():
    app = _app_sin_lifespan()

    @asynccontextmanager
    async def _conexion_que_falla():
        raise RuntimeError("no hay base real en este test")
        yield  # pragma: no cover -- nunca se alcanza

    motor_falso = MagicMock()
    motor_falso.connect.side_effect = lambda: _conexion_que_falla()
    app.state.motor = motor_falso

    client = TestClient(app)
    respuesta = client.get("/health/ready")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable"}
