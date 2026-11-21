import os

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.config import Settings
from app.infrastructure.externos import PasarelaStub
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo

from .dobles import SuscripcionesFalsas, solicitud

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]


@pytest.fixture
async def uow():
    motor = crear_motor(Settings())
    yield fabrica_unidad_de_trabajo(motor)
    await motor.dispose()


async def test_cobro_idempotente_con_un_solo_movimiento_y_outbox(uow):
    pedido = solicitud()

    primero = await casos_uso.cobrar_prima(uow, SuscripcionesFalsas(), PasarelaStub(), pedido)
    segundo = await casos_uso.cobrar_prima(uow, SuscripcionesFalsas(), PasarelaStub(), pedido)

    assert primero.creado and not segundo.creado
    assert segundo.pago.id == primero.pago.id
    assert (await casos_uso.consultar_pago(uow, primero.pago.id)).oferta_id == pedido.oferta_id
    async with uow() as tx:
        movimientos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.transaccion_pasarela WHERE idempotency_key = :k"),
            {"k": primero.pago.idempotency_key},
        )
        eventos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.outbox_evento WHERE agregado_id = :id"),
            {"id": primero.pago.id},
        )
    assert (movimientos, eventos) == (1, 1)


async def test_un_cobro_sin_moneda_explicita_en_la_fila_se_lee_como_cop(uow):
    pedido = solicitud(moneda="MXN")
    cobro = await casos_uso.cobrar_prima(uow, SuscripcionesFalsas(), PasarelaStub(), pedido)

    assert cobro.pago.moneda == "MXN"
    async with uow() as tx:
        await tx._sesion.execute(
            text(f"UPDATE {ESQUEMA}.pago SET moneda = DEFAULT WHERE pago_id = :id"),
            {"id": cobro.pago.id},
        )
        await tx.confirmar()
    assert (await casos_uso.consultar_pago(uow, cobro.pago.id)).moneda == "COP"
