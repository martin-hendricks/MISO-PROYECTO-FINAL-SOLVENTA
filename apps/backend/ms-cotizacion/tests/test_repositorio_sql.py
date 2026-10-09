import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import casos_uso_cotizaciones as casos_uso
from app.config import Settings
from app.infrastructure.catalogo_sql import CatalogoSQL
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]

DATOS_VALIDOS = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


@pytest.fixture
async def catalogo():
    motor = crear_motor(Settings())
    try:
        yield await CatalogoSQL.cargar(motor)
    finally:
        await motor.dispose()


async def test_recibir_solicitud_idempotente_y_outbox_en_la_misma_transaccion(uow, catalogo):
    clave = f"it-{uuid4()}"

    primero = await casos_uso.recibir_solicitud(
        uow, catalogo, clave, uuid4(), uuid4(), uuid4(), "soat-motocicleta", "app-socio", DATOS_VALIDOS
    )
    segundo = await casos_uso.recibir_solicitud(
        uow, catalogo, clave, uuid4(), uuid4(), uuid4(), "soat-motocicleta", "app-socio", DATOS_VALIDOS
    )

    assert primero.creada and not segundo.creada
    assert segundo.solicitud.id == primero.solicitud.id
    async with uow() as tx:
        eventos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.outbox_evento WHERE agregado_id = :id"),
            {"id": primero.solicitud.id},
        )
    assert eventos == 1
