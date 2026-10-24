import os
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.application.casos_uso import SolicitudEmision
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


async def test_consultar_poliza_por_numero(uow):
    emision = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), solicitud())

    encontrada = await casos_uso.consultar_poliza_por_numero(uow, emision.poliza.numero)

    assert encontrada.id == emision.poliza.id


async def test_listar_polizas_de_usuario_devuelve_las_del_usuario_mas_recientes_primero(uow):
    usuario_id = uuid4()
    pedido_1 = solicitud()
    pedido_1 = SolicitudEmision(
        solicitud_id=pedido_1.solicitud_id,
        oferta_id=pedido_1.oferta_id,
        usuario_id=usuario_id,
        token_pago_confirmado=pedido_1.token_pago_confirmado,
        coberturas=pedido_1.coberturas,
    )
    pedido_2 = solicitud()
    pedido_2 = SolicitudEmision(
        solicitud_id=pedido_2.solicitud_id,
        oferta_id=pedido_2.oferta_id,
        usuario_id=usuario_id,
        token_pago_confirmado=pedido_2.token_pago_confirmado,
        coberturas=pedido_2.coberturas,
    )

    await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), pedido_1)
    await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), pedido_2)

    listado = await casos_uso.listar_polizas_de_usuario(uow, usuario_id, limite=10)

    assert len(listado) == 2
    assert all(p.usuario_id == usuario_id for p in listado)
