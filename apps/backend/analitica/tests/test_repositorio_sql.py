import os
from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.config import Settings
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo
from app.ports.persistencia import EventoYaProcesado

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    async with motor.begin() as conn:
        await conn.execute(text(f"TRUNCATE {ESQUEMA}.conteo_eventos, {ESQUEMA}.evento_procesado"))
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


async def test_incrementar_crea_el_contador_y_persiste(uow):
    async with uow() as tx:
        await tx.metricas.incrementar(str(uuid4()), "PolizaEmitida", date(2026, 3, 1))
        await tx.confirmar()

    async with uow() as tx:
        conteos = await tx.metricas.listar(date(2026, 3, 1), date(2026, 3, 1))
    assert len(conteos) == 1
    assert conteos[0].cantidad == 1


async def test_incrementar_suma_sobre_el_mismo_tipo_y_fecha(uow):
    async with uow() as tx:
        await tx.metricas.incrementar(str(uuid4()), "PolizaEmitida", date(2026, 3, 1))
        await tx.confirmar()
    async with uow() as tx:
        await tx.metricas.incrementar(str(uuid4()), "PolizaEmitida", date(2026, 3, 1))
        await tx.confirmar()

    async with uow() as tx:
        conteos = await tx.metricas.listar(date(2026, 3, 1), date(2026, 3, 1))
    assert conteos[0].cantidad == 2


async def test_incrementar_mismo_evento_id_lanza_y_no_duplica(uow):
    evento_id = str(uuid4())
    async with uow() as tx:
        await tx.metricas.incrementar(evento_id, "PolizaEmitida", date(2026, 3, 1))
        await tx.confirmar()

    with pytest.raises(EventoYaProcesado):
        async with uow() as tx:
            await tx.metricas.incrementar(evento_id, "PolizaEmitida", date(2026, 3, 1))
            await tx.confirmar()

    async with uow() as tx:
        conteos = await tx.metricas.listar(date(2026, 3, 1), date(2026, 3, 1))
    assert conteos[0].cantidad == 1


async def test_listar_filtra_por_rango_de_fechas(uow):
    async with uow() as tx:
        await tx.metricas.incrementar(str(uuid4()), "PolizaEmitida", date(2026, 1, 1))
        await tx.metricas.incrementar(str(uuid4()), "PolizaEmitida", date(2026, 2, 1))
        await tx.confirmar()

    async with uow() as tx:
        conteos = await tx.metricas.listar(date(2026, 1, 1), date(2026, 1, 31))
    assert len(conteos) == 1
    assert conteos[0].fecha == date(2026, 1, 1)
