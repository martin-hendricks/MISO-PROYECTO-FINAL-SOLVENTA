import json
from uuid import uuid4

import httpx

from app.domain.modelos import DispositivoPush, Notificacion
from app.infrastructure.push_fcm import EnviadorFCM


def _notificacion(poliza="POL-1"):
    return Notificacion.crear(
        usuario_id=uuid4(),
        evento_origen_id=uuid4(),
        canal="push",
        tipo="poliza_renovada",
        titulo="Tu póliza fue renovada",
        cuerpo="La póliza POL-1 ahora vence el 2027-03-12.",
        destino="poliza-detalle",
        poliza=poliza,
    )


def _cliente(handler):
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


async def test_envia_mensaje_data_sin_bloque_notification():
    capturado = {}

    def handler(request: httpx.Request) -> httpx.Response:
        capturado["json"] = json.loads(request.content)
        capturado["auth"] = request.headers["authorization"]
        return httpx.Response(200, json={"name": "projects/demo/messages/1"})

    enviador = EnviadorFCM('{"project_id":"demo"}', _cliente(handler))
    enviador._token = "ya-valido"
    enviador._vence = __import__("datetime").datetime.now(__import__("datetime").UTC) + __import__(
        "datetime"
    ).timedelta(minutes=10)

    notificacion = _notificacion()
    dispositivo = DispositivoPush.registrar(notificacion.usuario_id, "android", "token-1")
    resultado = (await enviador.enviar_a_usuario([dispositivo], notificacion))[0]

    mensaje = capturado["json"]["message"]
    assert "notification" not in mensaje
    assert mensaje["fid"] == "token-1"
    assert "token" not in mensaje
    assert mensaje["data"]["poliza"] == "POL-1"
    assert mensaje["data"]["notificacionId"] == str(notificacion.notificacion_id)
    assert mensaje["android"]["priority"] == "HIGH"
    assert capturado["auth"] == "Bearer ya-valido"
    assert resultado.estado == "enviado"
    assert resultado.proveedor_id == "projects/demo/messages/1"


async def test_omite_poliza_cuando_no_hay():
    capturado = {}

    def handler(request: httpx.Request) -> httpx.Response:
        capturado["json"] = json.loads(request.content)
        return httpx.Response(200, json={"name": "projects/demo/messages/2"})

    enviador = EnviadorFCM('{"project_id":"demo"}', _cliente(handler))
    enviador._token = "ya-valido"
    from datetime import UTC, datetime, timedelta

    enviador._vence = datetime.now(UTC) + timedelta(minutes=10)
    notificacion = _notificacion(poliza=None)
    dispositivo = DispositivoPush.registrar(notificacion.usuario_id, "android", "token-1")
    await enviador.enviar_a_usuario([dispositivo], notificacion)

    assert "poliza" not in capturado["json"]["message"]["data"]


async def test_token_no_registrado_y_proveedor_caido():
    def no_registrado(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={"error": {"status": "NOT_FOUND", "details": [{"errorCode": "UNREGISTERED"}]}},
        )

    enviador = EnviadorFCM('{"project_id":"demo"}', _cliente(no_registrado))
    enviador._token = "ya-valido"
    from datetime import UTC, datetime, timedelta

    enviador._vence = datetime.now(UTC) + timedelta(minutes=10)
    notificacion = _notificacion()
    dispositivo = DispositivoPush.registrar(notificacion.usuario_id, "android", "token-malo")
    resultado = (await enviador.enviar_a_usuario([dispositivo], notificacion))[0]
    assert resultado.estado == "token_invalido"

    def caido(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": {"status": "UNAVAILABLE"}})

    enviador = EnviadorFCM('{"project_id":"demo"}', _cliente(caido))
    enviador._token = "ya-valido"
    enviador._vence = datetime.now(UTC) + timedelta(minutes=10)
    resultado = (await enviador.enviar_a_usuario([dispositivo], notificacion))[0]
    assert resultado.estado == "no_disponible"


async def test_argumento_invalido_tambien_es_token_invalido():
    def invalido(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            400,
            json={"error": {"status": "INVALID_ARGUMENT", "message": "The registration token is not valid"}},
        )

    from datetime import UTC, datetime, timedelta

    enviador = EnviadorFCM('{"project_id":"demo"}', _cliente(invalido))
    enviador._token = "ya-valido"
    enviador._vence = datetime.now(UTC) + timedelta(minutes=10)
    notificacion = _notificacion()
    dispositivo = DispositivoPush.registrar(notificacion.usuario_id, "android", "token-malo")
    resultado = (await enviador.enviar_a_usuario([dispositivo], notificacion))[0]
    assert resultado.estado == "token_invalido"


async def test_un_timeout_cuenta_como_no_disponible_y_el_token_se_renueva():
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("fcm")

    from datetime import UTC, datetime, timedelta

    enviador = EnviadorFCM('{"project_id":"demo"}', _cliente(timeout))
    enviador._token = "ya-valido"
    enviador._vence = datetime.now(UTC) + timedelta(minutes=10)
    notificacion = _notificacion()
    dispositivo = DispositivoPush.registrar(notificacion.usuario_id, "android", "token-1")
    resultado = (await enviador.enviar_a_usuario([dispositivo], notificacion))[0]
    assert resultado.estado == "no_disponible"

    class _Credenciales:
        token = "nuevo"
        expiry = datetime.now(UTC) + timedelta(hours=1)

        def refresh(self, request):
            return None

    import app.infrastructure.push_fcm as push_fcm

    original = push_fcm.service_account.Credentials.from_service_account_info
    push_fcm.service_account.Credentials.from_service_account_info = (
        lambda info, scopes: _Credenciales()
    )
    try:
        enviador._vence = datetime.now(UTC) - timedelta(minutes=1)
        assert await enviador._token_acceso() == "nuevo"
        assert await enviador._token_acceso() == "nuevo"
    finally:
        push_fcm.service_account.Credentials.from_service_account_info = original
