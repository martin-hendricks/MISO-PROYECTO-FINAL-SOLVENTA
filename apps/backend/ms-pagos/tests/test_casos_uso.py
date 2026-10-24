from decimal import Decimal
from uuid import uuid4

import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import EstadoPago, Pago, ResultadoPasarela
from app.infrastructure.externos import TOKEN_RECHAZO

from .dobles import solicitud


async def test_cobro_unico(uow, almacen, suscripciones, pasarela):
    # Dado una suscripción aceptada
    pedido = solicitud()

    # Cuando se ejecuta el cobro de la prima con su clave de idempotencia
    cobro = await casos_uso.cobrar_prima(uow, suscripciones, pasarela, pedido)

    # Entonces el movimiento simulado se registra una sola vez
    assert cobro.creado
    assert pasarela.movimientos == [f"cobro-prima:{pedido.oferta_id}"]
    assert list(almacen.pagos) == [cobro.pago.id]
    assert [e.tipo for e in almacen.eventos] == ["PagoPrimaRegistrado"]
    # Y el flujo continúa hacia la emisión
    assert cobro.pago.estado is EstadoPago.APROBADO
    assert (await casos_uso.consultar_pago(uow, cobro.pago.id)).estado is EstadoPago.APROBADO


async def test_reintento_con_la_misma_clave(uow, almacen, suscripciones, pasarela):
    # Dado un cobro ya ejecutado con su clave de idempotencia
    pedido = solicitud()
    original = await casos_uso.cobrar_prima(uow, suscripciones, pasarela, pedido)

    # Cuando se reintenta el cobro con la misma clave
    reintento = await casos_uso.cobrar_prima(uow, suscripciones, pasarela, pedido)

    # Entonces no se genera un segundo movimiento
    assert not reintento.creado
    assert len(pasarela.movimientos) == 1
    assert len(almacen.pagos) == 1 and len(almacen.eventos) == 1
    # Y se devuelve el resultado del cobro original
    assert (reintento.pago.id, reintento.pago.estado) == (original.pago.id, original.pago.estado)


async def test_el_cobro_fallido_queda_persistido_y_el_reintento_devuelve_el_fallo(uow, almacen, suscripciones, pasarela):
    pedido = solicitud(token=TOKEN_RECHAZO)

    fallido = await casos_uso.cobrar_prima(uow, suscripciones, pasarela, pedido)
    reintento = await casos_uso.cobrar_prima(uow, suscripciones, pasarela, pedido)

    assert fallido.pago.estado is EstadoPago.RECHAZADO
    assert almacen.pagos[fallido.pago.id].estado is EstadoPago.RECHAZADO
    assert reintento.pago.id == fallido.pago.id and len(pasarela.movimientos) == 1


async def test_sin_suscripcion_aceptada_no_se_cobra(uow, almacen, suscripciones, pasarela):
    suscripciones.respuesta = False

    with pytest.raises(ReglaDeNegocioViolada) as error:
        await casos_uso.cobrar_prima(uow, suscripciones, pasarela, solicitud())

    assert error.value.codigo == "suscripcion_no_aceptada"
    assert pasarela.movimientos == [] and almacen.pagos == {}


async def test_monto_invalido_no_llega_a_la_pasarela(uow, suscripciones, pasarela):
    with pytest.raises(ReglaDeNegocioViolada):
        await casos_uso.cobrar_prima(uow, suscripciones, pasarela, solicitud(monto="0"))

    assert pasarela.movimientos == []


async def test_cobro_concurrente_devuelve_el_pago_ganador(uow, almacen, suscripciones, pasarela):
    pedido = solicitud()
    ganador = Pago.registrar_prima(
        pedido.oferta_id, pedido.usuario_id, Decimal("1"), ResultadoPasarela(EstadoPago.APROBADO, "stub", "g")
    )
    almacen.chocar_en_proximo_commit = ganador

    cobro = await casos_uso.cobrar_prima(uow, suscripciones, pasarela, pedido)

    assert not cobro.creado
    assert cobro.pago.id == ganador.id
    assert almacen.eventos == []


async def test_choque_sin_pago_visible_falla(uow, almacen, suscripciones, pasarela):
    almacen.chocar_en_proximo_commit = Pago.registrar_prima(
        uuid4(), uuid4(), Decimal("1"), ResultadoPasarela(EstadoPago.APROBADO, "stub", "g")
    )

    with pytest.raises(RuntimeError, match="sin pago visible"):
        await casos_uso.cobrar_prima(uow, suscripciones, pasarela, solicitud())


async def test_consultar_pago_inexistente(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_pago(uow, uuid4())
