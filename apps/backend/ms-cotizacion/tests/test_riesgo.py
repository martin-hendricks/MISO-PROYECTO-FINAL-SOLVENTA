from decimal import Decimal

import pytest

from app.config import Settings
from app.domain.rating import ResultadoPrima
from app.domain.riesgo import FactorRiesgo, OrigenFactorRiesgo, aplicar_factor_riesgo
from app.infrastructure.adaptador_perfil_stub import AdaptadorPerfilRiesgoStub
from app.application import casos_uso

RESULTADO_BASE = ResultadoPrima(prima_neta=Decimal("100.00"), gastos_expedicion=Decimal("10.00"), moneda="COP")


@pytest.mark.parametrize("valor", [Decimal("1.0"), Decimal("1.5"), Decimal("0.8")])
def test_aplicar_factor_riesgo_es_determinista(valor):
    factor = FactorRiesgo(valor=valor, origen=OrigenFactorRiesgo.REAL)

    primero = aplicar_factor_riesgo(RESULTADO_BASE, factor)
    segundo = aplicar_factor_riesgo(RESULTADO_BASE, factor)

    assert primero == segundo
    assert primero.gastos_expedicion == RESULTADO_BASE.gastos_expedicion


def _config(timeout_ms: int = 20) -> Settings:
    return Settings(factor_riesgo_timeout_maximo_ms=timeout_ms, factor_riesgo_valor_respaldo=Decimal("1.0"))


async def test_stub_responde_a_tiempo_usa_factor_real():
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=1, factor_fijo=Decimal("1.3"))

    resultado, factor = await casos_uso.combinar_factor_riesgo(
        _config(), adaptador, usuario_id=None, producto="soat-motocicleta", resultado=RESULTADO_BASE
    )

    assert factor.origen == OrigenFactorRiesgo.REAL
    assert factor.valor == Decimal("1.3")
    assert resultado.prima_neta == Decimal("130.00")


async def test_stub_excede_tiempo_limite_usa_valor_de_respaldo():
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=50)

    resultado, factor = await casos_uso.combinar_factor_riesgo(
        _config(timeout_ms=10), adaptador, usuario_id=None, producto="soat-motocicleta", resultado=RESULTADO_BASE
    )

    assert factor.origen == OrigenFactorRiesgo.RESPALDO
    assert factor.valor == Decimal("1.0")
    assert resultado.prima_neta == RESULTADO_BASE.prima_neta


async def test_stub_falla_usa_valor_de_respaldo():
    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=0, fallar=True)

    resultado, factor = await casos_uso.combinar_factor_riesgo(
        _config(), adaptador, usuario_id=None, producto="soat-motocicleta", resultado=RESULTADO_BASE
    )

    assert factor.origen == OrigenFactorRiesgo.RESPALDO


async def test_timeout_cabe_dentro_del_presupuesto_configurado():
    import time

    adaptador = AdaptadorPerfilRiesgoStub(latencia_ms=100)
    config = _config(timeout_ms=15)

    inicio = time.monotonic()
    _, factor = await casos_uso.combinar_factor_riesgo(
        config, adaptador, usuario_id=None, producto="soat-motocicleta", resultado=RESULTADO_BASE
    )
    transcurrido_ms = (time.monotonic() - inicio) * 1000

    assert factor.origen == OrigenFactorRiesgo.RESPALDO
    assert transcurrido_ms <= config.factor_riesgo_timeout_maximo_ms + 50
