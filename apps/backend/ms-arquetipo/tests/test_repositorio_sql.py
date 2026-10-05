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


async def test_registro_idempotente_y_outbox_en_la_misma_transaccion(uow):
    clave = f"it-{uuid4()}"

    primero = await casos_uso.registrar_ejemplo(uow, clave, "REF-IT", Decimal("42.10"))
    segundo = await casos_uso.registrar_ejemplo(uow, clave, "REF-IT", Decimal("42.10"))

    assert primero.creado and not segundo.creado
    assert segundo.ejemplo.id == primero.ejemplo.id
    async with uow() as tx:
        eventos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.outbox_evento WHERE agregado_id = :id"),
            {"id": primero.ejemplo.id},
        )
    assert eventos == 1


async def test_aprobar_persiste_estado(uow):
    registro = await casos_uso.registrar_ejemplo(uow, f"it-{uuid4()}", "REF-IT", Decimal("1"))
    await casos_uso.aprobar_ejemplo(uow, registro.ejemplo.id)

    assert (await casos_uso.consultar_ejemplo(uow, registro.ejemplo.id)).estado == "aprobado"
