from decimal import Decimal
from uuid import uuid4

import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado
from app.domain.modelos import Ejemplo


async def test_registrar_publica_evento_en_outbox(uow, almacen):
    resultado = await casos_uso.registrar_ejemplo(uow, "clave-0001", "REF-1", Decimal("100"))

    assert resultado.creado
    assert [e.tipo for e in almacen.eventos] == ["EjemploRegistrado"]


async def test_reintento_con_la_misma_clave_no_duplica(uow, almacen):
    primero = await casos_uso.registrar_ejemplo(uow, "clave-0001", "REF-1", Decimal("100"))
    segundo = await casos_uso.registrar_ejemplo(uow, "clave-0001", "REF-1", Decimal("100"))

    assert not segundo.creado
    assert segundo.ejemplo.id == primero.ejemplo.id
    assert len(almacen.ejemplos) == 1
    assert len(almacen.eventos) == 1


async def test_carrera_de_idempotencia_devuelve_el_ganador(uow, almacen):
    ganador = Ejemplo.registrar("clave-0001", "REF-GANADOR", Decimal("5"))
    almacen.chocar_en_proximo_commit = ganador

    resultado = await casos_uso.registrar_ejemplo(uow, "clave-0001", "REF-PERDEDOR", Decimal("5"))

    assert not resultado.creado
    assert resultado.ejemplo.id == ganador.id
    assert almacen.eventos == []


async def test_aprobar_publica_evento(uow, almacen):
    registro = await casos_uso.registrar_ejemplo(uow, "clave-0001", "REF-1", Decimal("100"))

    aprobado = await casos_uso.aprobar_ejemplo(uow, registro.ejemplo.id)

    assert aprobado.estado == "aprobado"
    assert [e.tipo for e in almacen.eventos] == ["EjemploRegistrado", "EjemploAprobado"]


async def test_consultar_o_aprobar_inexistente(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_ejemplo(uow, uuid4())
    with pytest.raises(NoEncontrado):
        await casos_uso.aprobar_ejemplo(uow, uuid4())


async def test_indicadores(uow):
    await casos_uso.registrar_ejemplo(uow, "clave-0001", "A", Decimal("10"))
    await casos_uso.registrar_ejemplo(uow, "clave-0002", "B", Decimal("2.5"))

    resultado = await casos_uso.calcular_indicadores(uow)

    assert (resultado.total, resultado.monto_total) == (2, Decimal("12.5"))
