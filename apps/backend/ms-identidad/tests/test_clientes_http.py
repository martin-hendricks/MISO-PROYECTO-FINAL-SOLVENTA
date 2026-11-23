import httpx

from app.infrastructure.consentimiento_http import ClienteConsentimientoHTTP
from app.infrastructure.perfilamiento_http import ClientePerfilamientoHTTP


def _cliente_http(manejador) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(manejador), base_url="http://servicio")


# --- ClienteConsentimientoHTTP (ms-consentimiento / habeas data) ------------


async def test_consentimiento_vigente_true_cuando_responde_200_vigente_true():
    def manejador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"vigente": True, "revocado_en": None})

    cliente = ClienteConsentimientoHTTP(_cliente_http(manejador), "test-secret")

    assert await cliente.vigente("cliente-1") is True


async def test_consentimiento_vigente_false_cuando_responde_200_vigente_false():
    def manejador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"vigente": False, "revocado_en": "2026-01-01T00:00:00Z"})

    cliente = ClienteConsentimientoHTTP(_cliente_http(manejador), "test-secret")

    assert await cliente.vigente("cliente-1") is False


async def test_consentimiento_vigente_false_cuando_responde_404():
    """El 404 no distingue "nunca otorgado" de "revocado" (ver docstring del
    puerto); este adaptador trata ambos casos igual: sin habeas data vigente."""

    def manejador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"codigo": "no_encontrado", "mensaje": "No existe"})

    cliente = ClienteConsentimientoHTTP(_cliente_http(manejador), "test-secret")

    assert await cliente.vigente("cliente-1") is False


async def test_consentimiento_degrada_a_false_si_el_servicio_no_responde():
    def manejador(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no se pudo conectar")

    cliente = ClienteConsentimientoHTTP(_cliente_http(manejador), "test-secret")

    assert await cliente.vigente("cliente-1") is False


async def test_consentimiento_degrada_a_false_si_el_servicio_responde_5xx():
    def manejador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503)

    cliente = ClienteConsentimientoHTTP(_cliente_http(manejador), "test-secret")

    assert await cliente.vigente("cliente-1") is False


async def test_consentimiento_degrada_a_false_si_el_cuerpo_no_es_json():
    def manejador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"no es json")

    cliente = ClienteConsentimientoHTTP(_cliente_http(manejador), "test-secret")

    assert await cliente.vigente("cliente-1") is False


async def test_consentimiento_consulta_la_ruta_esperada():
    capturado = {}

    def manejador(request: httpx.Request) -> httpx.Response:
        capturado["path"] = request.url.path
        return httpx.Response(200, json={"vigente": True})

    cliente = ClienteConsentimientoHTTP(_cliente_http(manejador), "test-secret")
    await cliente.vigente("cliente-123")

    assert capturado["path"] == "/v1/consentimientos/cliente-123"


# --- ClientePerfilamientoHTTP (ms-perfilamiento / originación hipotecaria) --


async def test_perfilamiento_pendiente_true_cuando_hay_originacion_abierta():
    def manejador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"id": "x", "cliente_id": "cliente-1", "pendiente": True})

    cliente = ClientePerfilamientoHTTP(_cliente_http(manejador))

    assert await cliente.tiene_originacion_pendiente("cliente-1") is True


async def test_perfilamiento_pendiente_false_cuando_responde_404():
    def manejador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"codigo": "no_encontrado", "mensaje": "No existe"})

    cliente = ClientePerfilamientoHTTP(_cliente_http(manejador))

    assert await cliente.tiene_originacion_pendiente("cliente-1") is False


async def test_perfilamiento_degrada_a_false_si_el_servicio_no_responde():
    def manejador(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("tardó demasiado")

    cliente = ClientePerfilamientoHTTP(_cliente_http(manejador))

    assert await cliente.tiene_originacion_pendiente("cliente-1") is False


async def test_perfilamiento_degrada_a_false_si_el_servicio_responde_5xx():
    def manejador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    cliente = ClientePerfilamientoHTTP(_cliente_http(manejador))

    assert await cliente.tiene_originacion_pendiente("cliente-1") is False


async def test_perfilamiento_degrada_a_false_si_el_cuerpo_no_es_json():
    def manejador(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"no es json")

    cliente = ClientePerfilamientoHTTP(_cliente_http(manejador))

    assert await cliente.tiene_originacion_pendiente("cliente-1") is False


async def test_perfilamiento_consulta_la_ruta_esperada():
    capturado = {}

    def manejador(request: httpx.Request) -> httpx.Response:
        capturado["path"] = request.url.path
        return httpx.Response(404)

    cliente = ClientePerfilamientoHTTP(_cliente_http(manejador))
    await cliente.tiene_originacion_pendiente("cliente-123")

    assert capturado["path"] == "/v1/originaciones/clientes/cliente-123/pendiente"
