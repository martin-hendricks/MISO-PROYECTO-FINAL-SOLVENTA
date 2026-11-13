import pytest

from app.application import casos_uso
from app.domain.errores import NoEncontrado


async def test_otorgar_crea_consentimiento_la_primera_vez(uow, almacen):
    resultado = await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    assert resultado.creado
    assert resultado.consentimiento.cliente_id == "cliente-1"
    assert resultado.consentimiento.vigente
    assert len(almacen.consentimientos) == 1


async def test_otorgar_es_idempotente_si_ya_hay_uno_vigente(uow, almacen):
    primero = await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    segundo = await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    assert primero.creado
    assert not segundo.creado
    assert segundo.consentimiento.id == primero.consentimiento.id
    assert len(almacen.consentimientos) == 1


async def test_otorgar_de_nuevo_tras_revocar_crea_uno_nuevo(uow, almacen):
    primero = await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    await casos_uso.revocar_consentimiento(uow, "cliente-1")

    segundo = await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    assert segundo.creado
    assert segundo.consentimiento.id != primero.consentimiento.id
    assert segundo.consentimiento.vigente
    assert len(almacen.consentimientos) == 2


async def test_consultar_vigente_devuelve_el_otorgado(uow):
    otorgado = await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    consultado = await casos_uso.consultar_consentimiento_vigente(uow, "cliente-1")

    assert consultado.id == otorgado.consentimiento.id
    assert consultado.vigente


async def test_consultar_vigente_sin_consentimiento_es_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_consentimiento_vigente(uow, "cliente-inexistente")


async def test_revocar_marca_no_vigente_y_deja_de_poderse_consultar(uow):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    revocado = await casos_uso.revocar_consentimiento(uow, "cliente-1")

    assert not revocado.vigente
    assert revocado.revocado_en is not None
    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_consentimiento_vigente(uow, "cliente-1")


async def test_revocar_sin_consentimiento_vigente_es_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.revocar_consentimiento(uow, "cliente-inexistente")


async def test_revocar_dos_veces_la_segunda_es_no_encontrado(uow):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    await casos_uso.revocar_consentimiento(uow, "cliente-1")

    with pytest.raises(NoEncontrado):
        await casos_uso.revocar_consentimiento(uow, "cliente-1")


async def test_clientes_distintos_son_independientes(uow, almacen):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    await casos_uso.otorgar_consentimiento(uow, "cliente-2")
    await casos_uso.revocar_consentimiento(uow, "cliente-1")

    with pytest.raises(NoEncontrado):
        await casos_uso.consultar_consentimiento_vigente(uow, "cliente-1")
    assert (await casos_uso.consultar_consentimiento_vigente(uow, "cliente-2")).vigente
