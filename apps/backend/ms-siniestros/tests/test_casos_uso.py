from decimal import Decimal
from uuid import uuid4

import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado, TransicionInvalida
from app.domain.modelos import EstadoSiniestro, EvaluacionUmbral, EventoParametrico, Siniestro


# --- HU-32/33/34: ingesta encadenada -----------------------------------------------


async def test_ingerir_evento_con_umbral_cumplido_dispara_pago_y_marca_pagado(uow, almacen, adaptador_desembolso):
    resultado = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-1", Decimal("100"), Decimal("80"), True, Decimal("500.00")
    )

    assert resultado.procesado is True
    assert resultado.evaluacion.decision is True
    assert resultado.pago is not None
    assert resultado.pago.monto == Decimal("500.00")
    assert resultado.siniestro.estado is EstadoSiniestro.PAGADO
    assert adaptador_desembolso.desembolsos == [("evt-1", Decimal("500.00"))]


async def test_ingerir_evento_con_umbral_no_cumplido_no_paga_y_queda_decidido(uow, almacen, adaptador_desembolso):
    resultado = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-1", Decimal("10"), Decimal("80"), True, Decimal("500.00")
    )

    assert resultado.evaluacion.decision is False
    assert resultado.evaluacion.motivo == "umbral_no_alcanzado"
    assert resultado.pago is None
    assert resultado.siniestro.estado is EstadoSiniestro.DECIDIDO
    assert adaptador_desembolso.desembolsos == []


async def test_poliza_no_vigente_no_dispara_pago(uow, almacen, adaptador_desembolso):
    resultado = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-1", Decimal("999"), Decimal("80"), False, Decimal("500.00")
    )

    assert resultado.evaluacion.decision is False
    assert resultado.evaluacion.motivo == "poliza_no_vigente"
    assert resultado.pago is None


async def test_reingesta_del_mismo_evento_no_duplica_evaluacion_ni_pago(uow, almacen, adaptador_desembolso):
    primero = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-1", Decimal("100"), Decimal("80"), True, Decimal("500.00")
    )
    segundo = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-1", Decimal("100"), Decimal("80"), True, Decimal("500.00")
    )

    assert primero.procesado is True
    assert segundo.procesado is False
    assert segundo.siniestro.id == primero.siniestro.id
    assert segundo.pago.id == primero.pago.id
    # Un solo desembolso, no dos.
    assert adaptador_desembolso.desembolsos == [("evt-1", Decimal("500.00"))]
    assert len(almacen.pagos) == 1
    assert len(almacen.siniestros) == 1


async def test_reingesta_mantiene_el_mismo_siniestro_persistido(uow, almacen, adaptador_desembolso):
    await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-1", Decimal("10"), Decimal("80"), True, Decimal("500.00")
    )
    resultado = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-1", Decimal("10"), Decimal("80"), True, Decimal("500.00")
    )

    assert resultado.procesado is False
    assert resultado.pago is None
    assert len(almacen.siniestros) == 1


async def test_evento_sin_id_se_rechaza_y_no_persiste_nada(uow, almacen, adaptador_desembolso):
    with pytest.raises(Exception):
        await casos_uso.recibir_evento_parametrico(
            uow, adaptador_desembolso, "", Decimal("10"), Decimal("80"), True, Decimal("500.00")
        )

    assert almacen.eventos_parametricos == {}
    assert almacen.siniestros == {}


# --- HU-33 aislada: evaluar_umbral -------------------------------------------------


async def test_evaluar_umbral_persiste_resultado_sin_pagar(uow, almacen, adaptador_desembolso):
    await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-2", Decimal("5"), Decimal("80"), True, Decimal("1")
    )

    evaluacion = almacen.evaluaciones["evt-2"]
    assert evaluacion.decision is False
    assert evaluacion.umbral == Decimal("80")
    assert evaluacion.valor == Decimal("5")


# --- HU-34 aislada: disparar_pago_parametrico --------------------------------------


async def test_disparar_pago_parametrico_es_idempotente_por_evento(uow, almacen, adaptador_desembolso):
    evento = EventoParametrico.recibir("evt-3", Decimal("100"))
    siniestro = Siniestro.recibir("evt-3", origen="api")
    evaluacion = EvaluacionUmbral.evaluar(evento, Decimal("80"), True)

    async with uow() as tx:
        await tx.siniestros.agregar(siniestro)
        await tx.confirmar()

    primero = await casos_uso.disparar_pago_parametrico(uow, adaptador_desembolso, siniestro.id, evaluacion, Decimal("300"))
    segundo = await casos_uso.disparar_pago_parametrico(uow, adaptador_desembolso, siniestro.id, evaluacion, Decimal("300"))

    assert primero.id == segundo.id
    assert len(adaptador_desembolso.desembolsos) == 1


# --- HU-30: cambiar_estado_siniestro ------------------------------------------------


async def test_cambiar_estado_siniestro_inexistente_lanza_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.cambiar_estado_siniestro(uow, uuid4(), EstadoSiniestro.EN_EVALUACION, "operador")


async def test_cambiar_estado_invalido_no_persiste_cambio(uow, almacen, adaptador_desembolso):
    resultado = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-4", Decimal("10"), Decimal("80"), True, Decimal("1")
    )
    siniestro_id = resultado.siniestro.id  # queda en DECIDIDO (umbral no cumplido)

    with pytest.raises(TransicionInvalida):
        await casos_uso.cambiar_estado_siniestro(uow, siniestro_id, EstadoSiniestro.PAGADO, "operador")

    siniestro_actual = await casos_uso.consultar_siniestro(uow, siniestro_id)
    assert siniestro_actual.estado is EstadoSiniestro.DECIDIDO


async def test_cambiar_estado_valido_agrega_transicion_con_origen(uow, almacen, adaptador_desembolso):
    resultado = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-5", Decimal("10"), Decimal("80"), True, Decimal("1")
    )
    siniestro_id = resultado.siniestro.id

    siniestro = await casos_uso.cambiar_estado_siniestro(uow, siniestro_id, EstadoSiniestro.ENRUTADO, "operador-9")

    assert siniestro.estado is EstadoSiniestro.ENRUTADO
    assert siniestro.historial[-1].origen == "operador-9"


async def test_consultar_siniestro_inexistente_lanza_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_siniestro(uow, uuid4())


async def test_listar_siniestros(uow, almacen, adaptador_desembolso):
    await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-a", Decimal("10"), Decimal("80"), True, Decimal("1")
    )
    await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-b", Decimal("10"), Decimal("80"), True, Decimal("1")
    )

    siniestros = await casos_uso.listar_siniestros(uow, 10)

    assert len(siniestros) == 2


# --- HU-61 (back-office): siniestros abiertos de una póliza ------------------------


async def test_listar_siniestros_abiertos_de_poliza_excluye_pagados(uow, almacen, adaptador_desembolso):
    poliza_id = uuid4()
    # umbral cumplido -> termina en PAGADO (no es "abierto")
    pagado = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-pagado", Decimal("100"), Decimal("80"), True, Decimal("1"), poliza_id
    )
    # umbral no cumplido -> termina en DECIDIDO (sí es "abierto")
    abierto = await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-abierto", Decimal("10"), Decimal("80"), True, Decimal("1"), poliza_id
    )
    assert pagado.siniestro.estado is EstadoSiniestro.PAGADO
    assert abierto.siniestro.estado is EstadoSiniestro.DECIDIDO

    abiertos = await casos_uso.listar_siniestros_abiertos_de_poliza(uow, poliza_id)

    assert [s.id for s in abiertos] == [abierto.siniestro.id]


async def test_listar_siniestros_abiertos_de_poliza_sin_siniestros_devuelve_vacio(uow):
    assert await casos_uso.listar_siniestros_abiertos_de_poliza(uow, uuid4()) == []


async def test_listar_siniestros_abiertos_no_incluye_los_de_otra_poliza(uow, almacen, adaptador_desembolso):
    propia, ajena = uuid4(), uuid4()
    await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-propia", Decimal("10"), Decimal("80"), True, Decimal("1"), propia
    )
    await casos_uso.recibir_evento_parametrico(
        uow, adaptador_desembolso, "evt-ajena", Decimal("10"), Decimal("80"), True, Decimal("1"), ajena
    )

    abiertos = await casos_uso.listar_siniestros_abiertos_de_poliza(uow, propia)

    assert len(abiertos) == 1 and abiertos[0].evento_id == "evt-propia"
