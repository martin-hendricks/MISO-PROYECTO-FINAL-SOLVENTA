from decimal import Decimal
from uuid import uuid4

import httpx
import pytest

from app.application import casos_uso_cotizaciones as casos_uso
from app.config import Settings
from app.domain.rating import ResultadoPrima
from app.domain.riesgo import OrigenFactorRiesgo
from app.infrastructure.adaptador_perfil_perfilamiento import (
    AdaptadorPerfilRiesgoPerfilamiento,
    AdaptadorPerfilRiesgoPorProducto,
)
from app.infrastructure.adaptador_perfil_stub import AdaptadorPerfilRiesgoStub

RESULTADO_BASE = ResultadoPrima(prima_neta=Decimal("150000.00"), gastos_expedicion=Decimal("12000.00"), moneda="COP")


def _adaptador(responder) -> tuple[AdaptadorPerfilRiesgoPerfilamiento, list[httpx.Request]]:
    peticiones: list[httpx.Request] = []

    def manejar(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        return responder(request)

    http = httpx.AsyncClient(transport=httpx.MockTransport(manejar), base_url="http://ms-perfilamiento")
    return AdaptadorPerfilRiesgoPerfilamiento(http), peticiones


async def test_lee_el_factor_de_la_ultima_oferta_del_cliente():
    usuario_id = uuid4()
    adaptador, peticiones = _adaptador(lambda _: httpx.Response(200, json={"factor_ajuste": "0.854"}))

    factor = await adaptador.obtener_factor(usuario_id, "vida-crediticia")

    assert factor == Decimal("0.854")
    assert peticiones[0].method == "GET"
    assert peticiones[0].url.path == f"/v1/ofertas-hipotecario/clientes/{usuario_id}/ultima"


@pytest.mark.parametrize("estado", [403, 404, 503])
async def test_respuesta_no_exitosa_se_propaga(estado):
    adaptador, _ = _adaptador(lambda _: httpx.Response(estado, json={"codigo": "x", "mensaje": "x"}))

    with pytest.raises(httpx.HTTPStatusError):
        await adaptador.obtener_factor(uuid4(), "vida-crediticia")


@pytest.mark.parametrize("cuerpo", [{"factor_ajuste": "0"}, {"factor_ajuste": "-1.2"}, {"factor_ajuste": "nan?"}, {}])
async def test_factor_invalido_se_rechaza(cuerpo):
    adaptador, _ = _adaptador(lambda _: httpx.Response(200, json=cuerpo))

    with pytest.raises(ValueError):
        await adaptador.obtener_factor(uuid4(), "vida-crediticia")


async def test_por_producto_solo_consulta_perfilamiento_para_vida_crediticia():
    perfilamiento, peticiones = _adaptador(lambda _: httpx.Response(200, json={"factor_ajuste": "0.9"}))
    adaptador = AdaptadorPerfilRiesgoPorProducto(
        {"vida-crediticia": perfilamiento}, por_defecto=AdaptadorPerfilRiesgoStub(factor_fijo=Decimal("1.1"))
    )

    assert await adaptador.obtener_factor(uuid4(), "soat-motocicleta") == Decimal("1.1")
    assert peticiones == []
    assert await adaptador.obtener_factor(uuid4(), "vida-crediticia") == Decimal("0.9")
    assert len(peticiones) == 1


async def test_cotizar_vida_crediticia_usa_el_perfil_de_perfilamiento():
    adaptador, _ = _adaptador(lambda _: httpx.Response(200, json={"factor_ajuste": "0.854"}))

    resultado, factor = await casos_uso.combinar_factor_riesgo(
        Settings(), adaptador, usuario_id=uuid4(), producto="vida-crediticia", resultado=RESULTADO_BASE
    )

    assert factor.origen == OrigenFactorRiesgo.REAL
    assert resultado.prima_neta == Decimal("128100.00")
    assert resultado.gastos_expedicion == RESULTADO_BASE.gastos_expedicion


async def test_sin_consentimiento_degrada_con_valor_de_respaldo():
    adaptador, _ = _adaptador(
        lambda _: httpx.Response(403, json={"codigo": "consentimiento_no_otorgado", "mensaje": "x"})
    )

    resultado, factor = await casos_uso.combinar_factor_riesgo(
        Settings(), adaptador, usuario_id=uuid4(), producto="vida-crediticia", resultado=RESULTADO_BASE
    )

    assert factor.origen == OrigenFactorRiesgo.RESPALDO
    assert resultado.prima_neta == RESULTADO_BASE.prima_neta


async def test_perfilamiento_caido_degrada_con_valor_de_respaldo():
    def caido(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("conexión rechazada", request=request)

    adaptador, _ = _adaptador(caido)

    _, factor = await casos_uso.combinar_factor_riesgo(
        Settings(), adaptador, usuario_id=uuid4(), producto="vida-crediticia", resultado=RESULTADO_BASE
    )

    assert factor.origen == OrigenFactorRiesgo.RESPALDO
