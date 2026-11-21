from decimal import Decimal

import pytest

from app.domain.precio import NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO
from app.infrastructure.cache_fuentes import CacheEnMemoria
from tests.dobles import AdaptadorConfigurable


@pytest.mark.asyncio
async def test_si_open_finance_cae_devuelve_la_respuesta_cacheada_de_la_misma_cedula(uow, config, adaptador_open_data):
    from app.application import casos_uso

    cache = CacheEnMemoria()
    cedula = "1012345678"
    vivo = AdaptadorConfigurable(
        {NIVEL_INGRESOS_ESTIMADO: Decimal("0.800"), SCORE_COMPORTAMIENTO: Decimal("0.700")}
    )
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    await casos_uso.perfilar_y_ofertar(
        uow, vivo, adaptador_open_data, config, "clave-cache-1", "cliente-1", cache, cedula
    )
    caido = AdaptadorConfigurable({}, fallar=True)
    resultado = await casos_uso.perfilar_y_ofertar(
        uow, caido, adaptador_open_data, config, "clave-cache-2", "cliente-1", cache, cedula
    )
    ingresos = next(a for a in resultado.oferta.snapshot_atributos if a.nombre == NIVEL_INGRESOS_ESTIMADO)
    assert ingresos.valor == Decimal("0.800")
    assert ingresos.modo == "CACHE"
    assert ingresos.degradado is False


@pytest.mark.asyncio
async def test_revocar_el_consentimiento_descarta_lo_cacheado_bajo_la_cedula(uow, config, adaptador_open_data):
    from app.application import casos_uso

    cache = CacheEnMemoria()
    cedula = "1012345678"
    vivo = AdaptadorConfigurable(
        {NIVEL_INGRESOS_ESTIMADO: Decimal("0.800"), SCORE_COMPORTAMIENTO: Decimal("0.700")}
    )
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")
    await casos_uso.perfilar_y_ofertar(
        uow, vivo, adaptador_open_data, config, "clave-rev-1", "cliente-1", cache, cedula
    )
    await casos_uso.revocar_consentimiento(uow, "cliente-1", cache)
    await casos_uso.otorgar_consentimiento(uow, "cliente-1")

    resultado = await casos_uso.perfilar_y_ofertar(
        uow, AdaptadorConfigurable({}, fallar=True), adaptador_open_data, config, "clave-rev-2", "cliente-1", cache, cedula
    )

    ingresos = next(a for a in resultado.oferta.snapshot_atributos if a.nombre == NIVEL_INGRESOS_ESTIMADO)
    assert ingresos.modo == "DEFAULT"
    assert ingresos.degradado is True


@pytest.mark.asyncio
async def test_revocar_no_toca_lo_cacheado_para_otro_consentimiento(uow, config, adaptador_open_data):
    from app.application import casos_uso

    cache = CacheEnMemoria()
    vivo = AdaptadorConfigurable(
        {NIVEL_INGRESOS_ESTIMADO: Decimal("0.800"), SCORE_COMPORTAMIENTO: Decimal("0.700")}
    )
    for cliente, cedula in (("cliente-1", "111"), ("cliente-2", "222")):
        await casos_uso.otorgar_consentimiento(uow, cliente)
        await casos_uso.perfilar_y_ofertar(
            uow, vivo, adaptador_open_data, config, f"clave-{cliente}", cliente, cache, cedula
        )

    await casos_uso.revocar_consentimiento(uow, "cliente-1", cache)

    assert await cache.obtener("OPEN_FINANCE", "111") is None
    assert await cache.obtener("OPEN_FINANCE", "222") is not None


@pytest.mark.asyncio
async def test_sin_cache_el_fallo_usa_el_valor_de_respaldo(uow, config, adaptador_open_data):
    from app.application import casos_uso

    await casos_uso.otorgar_consentimiento(uow, "cliente-2")
    resultado = await casos_uso.perfilar_y_ofertar(
        uow,
        AdaptadorConfigurable({}, fallar=True),
        adaptador_open_data,
        config,
        "clave-default",
        "cliente-2",
        CacheEnMemoria(),
        "1099888777",
    )
    ingresos = next(a for a in resultado.oferta.snapshot_atributos if a.nombre == NIVEL_INGRESOS_ESTIMADO)
    assert ingresos.modo == "DEFAULT"
    assert ingresos.degradado is True


async def test_la_purga_avisa_a_los_almacenes_compartidos_ademas_de_limpiar_la_memoria():
    from app.infrastructure.cache_fuentes import CacheFuentesConPurga

    purgados = []

    async def purga(consentimiento_id):
        purgados.append(consentimiento_id)
        return 2

    cache = CacheFuentesConPurga([purga])
    await cache.guardar("OPEN_FINANCE", "123", {"zona_riesgo": Decimal("0.5")}, "consentimiento-1")

    await cache.invalidar_consentimiento("consentimiento-1")

    assert purgados == ["consentimiento-1"]
    assert await cache.obtener("OPEN_FINANCE", "123") is None


async def test_si_la_purga_compartida_falla_la_memoria_queda_limpia_y_no_se_propaga(caplog):
    from app.infrastructure.cache_fuentes import CacheFuentesConPurga

    async def purga_caida(consentimiento_id):
        raise ConnectionError("redis caido")

    cache = CacheFuentesConPurga([purga_caida])
    await cache.guardar("OPEN_FINANCE", "123", {"zona_riesgo": Decimal("0.5")}, "consentimiento-1")

    with caplog.at_level("WARNING"):
        await cache.invalidar_consentimiento("consentimiento-1")

    assert await cache.obtener("OPEN_FINANCE", "123") is None
    assert "no se pudo purgar la cache compartida" in caplog.text
