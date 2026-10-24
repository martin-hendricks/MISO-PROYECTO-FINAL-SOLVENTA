import os

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.config import Settings
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo

from .dobles import CobrosFalsos, SuscripcionesFalsas, solicitud

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


async def test_emision_idempotente_con_coberturas_y_outbox_en_la_misma_transaccion(uow):
    pedido = solicitud()

    primera = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), pedido)
    segunda = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), pedido)

    assert primera.creada and not segunda.creada
    assert segunda.poliza.numero == primera.poliza.numero
    consultada = await casos_uso.consultar_poliza(uow, primera.poliza.id)
    assert len(consultada.coberturas) == 2
    async with uow() as tx:
        eventos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.outbox_evento WHERE agregado_id = :id"),
            {"id": primera.poliza.id},
        )
    assert eventos == 1


async def test_cada_oferta_recibe_un_numero_nuevo(uow):
    primera = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), solicitud())
    segunda = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), solicitud())

    assert primera.poliza.numero != segunda.poliza.numero
