from decimal import Decimal
from uuid import uuid4

import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado, ReglaNoConfigurada
from app.domain.modelos import Decision, Suscripcion

from .dobles import regla


async def test_evaluar_persiste_la_decision_y_su_evento_en_la_misma_transaccion(uow, almacen):
    solicitud = uuid4()

    resultado = await casos_uso.evaluar_suscripcion(uow, solicitud, uuid4(), Decimal("0.3"))

    assert resultado.creada
    assert almacen.suscripciones[resultado.suscripcion.id].decision is Decision.ACEPTADA
    assert [e.tipo for e in almacen.eventos] == ["SuscripcionDecidida"]


async def test_reevaluar_la_misma_solicitud_devuelve_la_decision_existente(uow, almacen):
    solicitud = uuid4()
    primera = await casos_uso.evaluar_suscripcion(uow, solicitud, uuid4(), Decimal("0.9"))

    segunda = await casos_uso.evaluar_suscripcion(uow, solicitud, uuid4(), Decimal("0.1"))

    assert not segunda.creada
    assert segunda.suscripcion.id == primera.suscripcion.id
    assert segunda.suscripcion.decision is Decision.RECHAZADA
    assert len(almacen.suscripciones) == 1
    assert len(almacen.eventos) == 1


async def test_carrera_entre_dos_evaluaciones_devuelve_la_ganadora(uow, almacen):
    solicitud = uuid4()
    ganadora = Suscripcion.decidir(solicitud, uuid4(), Decimal("0.2"), regla())
    almacen.chocar_en_proximo_commit = ganadora

    resultado = await casos_uso.evaluar_suscripcion(uow, solicitud, uuid4(), Decimal("0.2"))

    assert not resultado.creada
    assert resultado.suscripcion.id == ganadora.id
    assert almacen.eventos == []


async def test_sin_regla_vigente_no_decide(uow, almacen):
    almacen.regla = None

    with pytest.raises(ReglaNoConfigurada):
        await casos_uso.evaluar_suscripcion(uow, uuid4(), uuid4(), Decimal("0.1"))
    assert almacen.suscripciones == {}


async def test_consultar_solicitud_sin_decision_es_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_suscripcion(uow, uuid4())


async def test_consultar_devuelve_la_decision_persistida(uow):
    solicitud = uuid4()
    creada = await casos_uso.evaluar_suscripcion(uow, solicitud, uuid4(), Decimal("0.95"))

    consultada = await casos_uso.consultar_suscripcion(uow, solicitud)

    assert consultada.id == creada.suscripcion.id
    assert consultada.motivo == "Riesgo fuera del apetito"
