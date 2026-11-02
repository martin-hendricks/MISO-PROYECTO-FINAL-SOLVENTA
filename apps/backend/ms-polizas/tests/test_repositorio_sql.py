import os
from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import casos_uso
from app.application.casos_uso import SolicitudEmision
from app.config import Settings
from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import Cobertura
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo

from .dobles import CobrosFalsos, FirmaFalsa, SuscripcionesFalsas, solicitud

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

    primera = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(), pedido)
    segunda = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(), pedido)

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
    primera = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(), solicitud())
    segunda = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(), solicitud())

    assert primera.poliza.numero != segunda.poliza.numero


async def test_consultar_poliza_por_numero(uow):
    emision = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(), solicitud())

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

    await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(), pedido_1)
    await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(), pedido_2)

    listado = await casos_uso.listar_polizas_de_usuario(uow, usuario_id, limite=10)

    assert len(listado) == 2
    assert all(p.usuario_id == usuario_id for p in listado)


async def test_ciclo_de_vida_renovar_modificar_y_cancelar_persisten_contra_bd_real(uow):
    emitida = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(), solicitud())
    poliza_id = emitida.poliza.id
    assert emitida.poliza.prima.valor == sum(c.suma_asegurada for c in emitida.poliza.coberturas)

    nueva_fecha = date(emitida.poliza.fin_vigencia.year + 1, 1, 1)
    renovada = await casos_uso.renovar_poliza(uow, poliza_id, nueva_fecha)
    assert renovada.fin_vigencia == nueva_fecha

    modificada = await casos_uso.modificar_poliza(
        uow, poliza_id, [Cobertura(nombre="Robo", suma_asegurada=Decimal("1000"))]
    )
    assert [c.nombre for c in modificada.coberturas] == ["Robo"]

    cancelada = await casos_uso.cancelar_poliza(uow, poliza_id, "El cliente lo pidió", "op-1")
    assert cancelada.estado.value == "CANCELADA"
    assert cancelada.motivo_cancelacion == "El cliente lo pidió"
    assert cancelada.cancelada_por == "op-1"
    assert cancelada.devolucion_estimada is not None

    consultada = await casos_uso.consultar_poliza(uow, poliza_id)
    assert consultada.estado.value == "CANCELADA"
    assert consultada.cancelada_por == "op-1"
    assert [c.nombre for c in consultada.coberturas] == ["Robo"]
    # La prima no se toca en renovar/modificar/cancelar, sigue la de emisión.
    assert consultada.prima.valor == emitida.poliza.prima.valor

    async with uow() as tx:
        eventos = await tx._sesion.scalar(
            text(f"SELECT count(*) FROM {ESQUEMA}.outbox_evento WHERE agregado_id = :id"),
            {"id": poliza_id},
        )
    assert eventos == 4  # emitida + renovada + modificada + cancelada


async def test_firma_persiste_constancia_y_hash_en_la_poliza(uow):
    pedido = solicitud()

    emision = await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(), pedido)

    constancia = await casos_uso.consultar_firma(uow, pedido.oferta_id)
    assert constancia.exitosa and constancia.firmada_en.tzinfo is not None
    assert (await casos_uso.consultar_poliza(uow, emision.poliza.id)).firma_hash == constancia.firma_hash


async def test_firma_rechazada_persiste_constancia_sin_poliza(uow):
    pedido = solicitud()

    with pytest.raises(ReglaDeNegocioViolada):
        await casos_uso.emitir_poliza(uow, SuscripcionesFalsas(), CobrosFalsos(), FirmaFalsa(exitosa=False), pedido)

    constancia = await casos_uso.consultar_firma(uow, pedido.oferta_id)
    assert not constancia.exitosa and constancia.motivo
    async with uow() as tx:
        assert await tx.polizas.obtener_por_oferta(pedido.oferta_id) is None
