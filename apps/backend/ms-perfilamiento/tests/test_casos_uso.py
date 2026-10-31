from decimal import Decimal

import pytest

from app.application import casos_uso
from app.domain.errores import ConsentimientoNoOtorgado, NoEncontrado
from app.domain.modelos import Oferta, Perfil
from app.domain.precio import ANTIGUEDAD_DOCUMENTO, NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO, ZONA_RIESGO
from app.infrastructure.adaptadores import AdaptadorOpenDataStub, AdaptadorOpenFinanceStub

from .dobles import AdaptadorConfigurable


async def test_otorgar_consentimiento_publica_evento_y_es_idempotente(uow, almacen):
    primero = await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    segundo = await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    assert primero.creado
    assert primero.consentimiento.vigente
    assert not segundo.creado
    assert segundo.consentimiento.id == primero.consentimiento.id
    assert [e.tipo for e in almacen.eventos] == ["ConsentimientoPerfilamientoOtorgado"]


async def test_consultar_consentimiento_vigente(uow):
    assert await casos_uso.consultar_consentimiento_vigente(uow, "cliente-1") is None

    await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    vigente = await casos_uso.consultar_consentimiento_vigente(uow, "cliente-1")
    assert vigente is not None
    assert vigente.cliente_id == "cliente-1"


async def test_revocar_consentimiento_impide_futuras_consultas(uow, almacen):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    revocado = await casos_uso.revocar_consentimiento(uow, "cliente-1")

    assert not revocado.vigente
    assert await casos_uso.consultar_consentimiento_vigente(uow, "cliente-1") is None
    assert [e.tipo for e in almacen.eventos] == [
        "ConsentimientoPerfilamientoOtorgado",
        "ConsentimientoPerfilamientoRevocado",
    ]


async def test_revocar_sin_consentimiento_previo_es_no_encontrado(uow):
    with pytest.raises(NoEncontrado):
        await casos_uso.revocar_consentimiento(uow, "cliente-sin-consentimiento")


async def test_perfilar_sin_consentimiento_no_invoca_ningun_adaptador(uow, config):
    class _AdaptadorQueExplota:
        async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
            raise AssertionError("no debe invocarse sin consentimiento vigente")

    with pytest.raises(ConsentimientoNoOtorgado):
        await casos_uso.perfilar_y_ofertar(
            uow, _AdaptadorQueExplota(), _AdaptadorQueExplota(), config, "clave-0001", "cliente-sin-consentimiento"
        )


async def test_perfilar_con_consentimiento_vigente_arma_oferta_explicable(
    uow, config, adaptador_open_finance, adaptador_open_data
):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, adaptador_open_finance, adaptador_open_data, config, "clave-0001", "cliente-1"
    )

    assert resultado.creada
    assert not resultado.oferta.degradado
    assert resultado.oferta.precio > 0
    assert len(resultado.oferta.factores) == 4
    nombres_snapshot = {a.nombre for a in resultado.oferta.snapshot_atributos}
    assert nombres_snapshot == {NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO, ZONA_RIESGO, ANTIGUEDAD_DOCUMENTO}


def _oferta_ganadora() -> Oferta:
    perfil = Perfil.armar("cliente-1", [])
    return Oferta.armar("cliente-1", Decimal("10"), [], perfil)


async def test_choque_de_clave_devuelve_la_oferta_que_gano(uow, almacen, config, adaptador_open_finance, adaptador_open_data):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    ganadora = _oferta_ganadora()
    almacen.chocar_en_proximo_commit = ("clave-0001", ganadora)

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, adaptador_open_finance, adaptador_open_data, config, "clave-0001", "cliente-1"
    )

    assert not resultado.creada
    assert resultado.oferta.id == ganadora.id


async def test_choque_de_clave_sin_registro_visible_falla(uow, almacen, config, adaptador_open_finance, adaptador_open_data):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    almacen.chocar_en_proximo_commit = ("otra-clave", _oferta_ganadora())

    with pytest.raises(RuntimeError):
        await casos_uso.perfilar_y_ofertar(
            uow, adaptador_open_finance, adaptador_open_data, config, "clave-0001", "cliente-1"
        )


async def test_reintento_con_la_misma_clave_no_duplica_oferta(uow, config, adaptador_open_finance, adaptador_open_data):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    primero = await casos_uso.perfilar_y_ofertar(
        uow, adaptador_open_finance, adaptador_open_data, config, "clave-0001", "cliente-1"
    )
    segundo = await casos_uso.perfilar_y_ofertar(
        uow, adaptador_open_finance, adaptador_open_data, config, "clave-0001", "cliente-1"
    )

    assert not segundo.creada
    assert segundo.oferta.id == primero.oferta.id


async def test_adaptador_que_excede_el_timeout_degrada_con_valor_de_respaldo(uow, config, adaptador_open_data):
    """Ejercita el camino real de asyncio.wait_for expirando (HU-56): el adaptador de
    Open Finance tarda más que config.timeout_open_finance_ms, así que el caso de uso
    debe capturar el TimeoutError y sustituir por el valor de respaldo, marcando
    degradado=True para esos atributos sin cancelar la oferta."""
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    adaptador_lento = AdaptadorConfigurable(
        {NIVEL_INGRESOS_ESTIMADO: Decimal("0.9"), SCORE_COMPORTAMIENTO: Decimal("0.9")},
        lento=True,
    )

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, adaptador_lento, adaptador_open_data, config, "clave-timeout", "cliente-1"
    )

    assert resultado.creada
    assert resultado.oferta.degradado
    atributos_open_finance = [a for a in resultado.oferta.snapshot_atributos if a.origen.value == "open_finance"]
    assert all(a.degradado for a in atributos_open_finance)
    assert {a.nombre for a in atributos_open_finance} == {NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO}
    valor_respaldo_ingresos = next(a for a in atributos_open_finance if a.nombre == NIVEL_INGRESOS_ESTIMADO).valor
    assert valor_respaldo_ingresos == config.respaldo_nivel_ingresos_estimado


async def test_adaptador_que_falla_degrada_con_valor_de_respaldo(uow, config, adaptador_open_finance):
    """HU-56: un adaptador que lanza una excepción (en vez de tardar) también degrada,
    sin distinguir el tipo de fallo (ancho deliberado, igual que un timeout)."""
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    adaptador_que_falla = AdaptadorConfigurable({}, fallar=True)

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, adaptador_open_finance, adaptador_que_falla, config, "clave-fallo", "cliente-1"
    )

    assert resultado.creada
    assert resultado.oferta.degradado
    atributos_open_data = [a for a in resultado.oferta.snapshot_atributos if a.origen.value == "open_data"]
    assert all(a.degradado for a in atributos_open_data)
    assert {a.nombre for a in atributos_open_data} == {ZONA_RIESGO, ANTIGUEDAD_DOCUMENTO}


async def test_oferta_degradada_sigue_siendo_valida_y_no_cancela_originacion(
    uow, config, adaptador_open_finance
):
    """HU-55/HU-56: la originación no se cancela; la oferta se entrega igual, marcada."""
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    ambos_fallan_open_data = AdaptadorConfigurable({}, fallar=True)

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, adaptador_open_finance, ambos_fallan_open_data, config, "clave-no-cancela", "cliente-1"
    )

    assert resultado.oferta.precio > 0
    assert resultado.oferta.degradado is True


async def test_doble_de_open_finance_con_demora_forzada_degrada(uow, config):
    """HU-88: la demora configurada en el doble basta para ejercitar la degradación de HU-56."""
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    lento = AdaptadorOpenFinanceStub(latencia_ms=config.timeout_open_finance_ms * 4)

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, lento, AdaptadorOpenDataStub(), config, "clave-doble-lento", "cliente-1"
    )

    degradados = {a.origen.value for a in resultado.oferta.snapshot_atributos if a.degradado}
    assert degradados == {"open_finance"}


async def test_doble_de_open_data_con_fallo_forzado_degrada(uow, config):
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, AdaptadorOpenFinanceStub(), AdaptadorOpenDataStub(fallar=True), config, "clave-doble-falla", "cliente-1"
    )

    degradados = {a.origen.value for a in resultado.oferta.snapshot_atributos if a.degradado}
    assert degradados == {"open_data"}
