import os
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.config import Settings
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


async def test_evaluacion_idempotente_y_outbox_en_la_misma_transaccion(uow):
    solicitud = uuid4()

    primera = await casos_uso.evaluar_suscripcion(uow, solicitud, uuid4(), Decimal("0.2"))
    segunda = await casos_uso.evaluar_suscripcion(uow, solicitud, uuid4(), Decimal("0.2"))

    assert primera.creada and not segunda.creada
    assert segunda.suscripcion.id == primera.suscripcion.id
    async with uow() as tx:
        eventos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.outbox_evento WHERE agregado_id = :id"),
            {"id": primera.suscripcion.id},
        )
    assert eventos == 1


async def test_la_regla_vigente_se_lee_de_la_tabla(uow):
    resultado = await casos_uso.evaluar_suscripcion(uow, uuid4(), uuid4(), Decimal("0.99"))

    assert resultado.suscripcion.decision == "RECHAZADA"
    assert resultado.suscripcion.motivo == "Riesgo fuera del apetito de la aseguradora"
