"""Haversine y semilla contra PostgreSQL. Se omite sin DATABASE_URL."""

import os
from decimal import Decimal

import pytest
from sqlalchemy import text

from app.config import Settings
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo
from app.seguridad import Llamante
from uuid import uuid4

from app.application import prestadores as casos

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    async with motor.begin() as conexion:
        for archivo in (
            "db/01_ms_siniestros.sql",
            "db/08_ms_siniestros_prestadores.sql",
        ):
            # La semilla vive en 08 y asume el schema. El archivo 01 crea el schema.
            del archivo
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


@pytest.mark.asyncio
async def test_semilla_y_orden_cerca_de_chapinero(uow):
    motor = crear_motor(Settings())
    script = open("db/08_ms_siniestros_prestadores.sql").read()
    async with motor.begin() as conexion:
        await conexion.execute(text(script))
        await conexion.execute(text(script))
        ciudades = dict(
            (await conexion.execute(text("SELECT ciudad, count(*) FROM ms_siniestros.prestador GROUP BY ciudad"))).all()
        )
    await motor.dispose()
    assert ciudades["Bogotá"] == 30
    assert ciudades["Medellín"] == 20
    assert ciudades["Chía"] == 10
    cliente = Llamante(uid=uuid4(), rol="cliente", sub="a@solventa.co")
    resultado = await casos.buscar(
        uow,
        cliente,
        casos.ConsultaPrestadores(
            lat=Decimal("4.643200"), lng=Decimal("-74.063100"), ramo="soat-motocicleta", radio_km=Decimal("10")
        ),
    )
    assert resultado.prestadores
    assert resultado.prestadores[0].prestador.id == "PRE-BOG-06"
