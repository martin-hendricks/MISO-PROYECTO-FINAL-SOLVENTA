import httpx
import pytest
from fastapi import HTTPException

from app.clients.nucleo import ClienteNucleo, correlacion_saliente, token_saliente

RUTA = "/v1/originaciones/clientes/cli-1/pendiente"


def _cliente(manejador) -> ClienteNucleo:
    cliente = ClienteNucleo({})
    cliente._clientes["ms-perfilamiento"] = httpx.Client(
        base_url="http://perfilamiento", transport=httpx.MockTransport(manejador)
    )
    return cliente


@pytest.mark.parametrize("estado", [204, 404])
def test_cerrar_originacion_acepta_cerrada_o_inexistente(estado):
    peticiones = []

    def manejador(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        return httpx.Response(estado)

    token = token_saliente.set("tok-1")
    correlacion = correlacion_saliente.set("corr-1")
    try:
        assert _cliente(manejador).cerrar_originacion("cli-1") is None
    finally:
        token_saliente.reset(token)
        correlacion_saliente.reset(correlacion)

    assert len(peticiones) == 1
    assert peticiones[0].method == "DELETE"
    assert peticiones[0].url.path == RUTA
    assert peticiones[0].headers["Authorization"] == "Bearer tok-1"
    assert peticiones[0].headers["X-Correlation-Id"] == "corr-1"


def test_cerrar_originacion_sin_sesion_no_envia_cabeceras():
    peticiones = []

    def manejador(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        return httpx.Response(204)

    _cliente(manejador).cerrar_originacion("cli-1")

    assert "Authorization" not in peticiones[0].headers
    assert "X-Correlation-Id" not in peticiones[0].headers


def test_cerrar_originacion_con_error_del_servicio_es_503():
    with pytest.raises(HTTPException) as error:
        _cliente(lambda request: httpx.Response(500)).cerrar_originacion("cli-1")

    assert error.value.status_code == 503


def test_cerrar_originacion_sin_conexion_es_503():
    def manejador(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("sin red", request=request)

    with pytest.raises(HTTPException) as error:
        _cliente(manejador).cerrar_originacion("cli-1")

    assert error.value.status_code == 503


def test_cerrar_originacion_sin_url_configurada_es_503():
    with pytest.raises(HTTPException) as error:
        ClienteNucleo({}).cerrar_originacion("cli-1")

    assert error.value.status_code == 503
