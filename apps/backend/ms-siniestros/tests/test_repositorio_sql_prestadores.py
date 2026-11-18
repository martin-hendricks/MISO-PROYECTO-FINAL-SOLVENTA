"""Haversine, área visible y semilla contra PostgreSQL. Se omite sin DATABASE_URL."""

import os
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.application import prestadores as casos
from app.config import Settings
from app.domain.prestador import AreaVisible
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo
from app.seguridad import Llamante

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]

SCRIPTS = ("db/08_ms_siniestros_prestadores.sql", "db/09_ms_siniestros_prestadores_paises.sql")
CLIENTE = Llamante(uid=uuid4(), rol="cliente", sub="a@solventa.co")


async def _aplicar_semilla(motor) -> None:
    """Dos veces: los scripts deben poder repetirse sin duplicar filas."""
    async with motor.begin() as conexion:
        crudo = (await conexion.get_raw_connection()).driver_connection
        for _ in range(2):
            for archivo in SCRIPTS:
                await crudo.execute(open(archivo, encoding="utf-8").read())


@pytest.fixture
async def motor():
    motor = crear_motor(Settings())
    await _aplicar_semilla(motor)
    yield motor
    await motor.dispose()


@pytest.mark.asyncio
async def test_semilla_de_cuatro_paises(motor):
    async with motor.connect() as conexion:
        paises = dict(
            (await conexion.execute(text("SELECT pais, count(*) FROM ms_siniestros.prestador WHERE id LIKE 'PRE-%' AND creado_por = 'semilla' GROUP BY pais"))).all()
        )
        ciudades = (await conexion.execute(text("SELECT count(*) FROM ms_siniestros.ciudad_prestador"))).scalar()
        bogota = (await conexion.execute(text("SELECT pais FROM ms_siniestros.prestador WHERE id = 'PRE-BOG-06'"))).scalar()
    assert paises == {"CO": 60, "MX": 13, "CL": 13, "PE": 13}
    assert ciudades == 12
    assert bogota == "CO"


@pytest.mark.asyncio
async def test_orden_cerca_de_chapinero_y_area(motor):
    uow = fabrica_unidad_de_trabajo(motor)
    cerca = await casos.buscar(
        uow,
        CLIENTE,
        casos.ConsultaPrestadores(
            lat=Decimal("4.643200"), lng=Decimal("-74.063100"), ramo="soat-motocicleta", radio_km=Decimal("10")
        ),
    )
    assert [fila.prestador.id for fila in cerca.prestadores[:2]] == ["PRE-BOG-12", "PRE-BOG-06"]

    chapinero = AreaVisible(Decimal("4.6700"), Decimal("4.6300"), Decimal("-74.0500"), Decimal("-74.0700"))
    area = await casos.buscar(
        uow,
        CLIENTE,
        casos.ConsultaPrestadores(area=chapinero, lat=Decimal("4.6432"), lng=Decimal("-74.0631"), limite=500),
    )
    ids = [fila.prestador.id for fila in area.prestadores]
    assert "PRE-BOG-02" in ids and "PRE-BOG-06" in ids
    distancias = [fila.distancia_km for fila in area.prestadores]
    assert distancias == sorted(distancias)

    recortada = await casos.buscar(uow, CLIENTE, casos.ConsultaPrestadores(area=chapinero, limite=2))
    assert len(recortada.prestadores) == 2
    assert recortada.truncado is True

    mexico = await casos.ciudades(uow, CLIENTE, "MX")
    assert [(c.nombre, total) for c, total in mexico] == [("Ciudad de México", 5), ("Guadalajara", 4), ("Monterrey", 4)]


@pytest.mark.asyncio
async def test_ciudad_fuera_del_catalogo_viola_la_llave(motor):
    with pytest.raises(IntegrityError):
        async with motor.begin() as conexion:
            await conexion.execute(
                text(
                    "UPDATE ms_siniestros.prestador SET ciudad = 'Lima' WHERE id = 'PRE-BOG-06'"
                )
            )
