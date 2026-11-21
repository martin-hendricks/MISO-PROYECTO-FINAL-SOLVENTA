import json
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID

import httpx
import jwt
import pytest
from fastapi.testclient import TestClient

from app.clients.token_servicio import token_de_socio
from app.config import Settings
from app.clients.ms_perfilamiento import ClienteMsPerfilamiento
from app.dependencies import obtener_cliente_identidad, obtener_cliente_perfilamiento
from app.main import crear_app
from app.seguridad import Socio

from .conftest import CABECERA_SOLO_CATALOGO, REGISTRO_SOCIOS, SOCIO_ID

USUARIO_ID = "11111111-1111-1111-1111-111111111111"
CUERPO = {"tipoDocumento": "CC", "numeroDocumento": "1012345678", "valor": 180000000, "plazoMeses": 240}


def _cliente_registrado(identidad):
    identidad.respuestas[("GET", "/v1/usuarios/documento")] = lambda _: httpx.Response(
        200, json={"usuario_id": USUARIO_ID}
    )


def _perfilamiento_acepta(perfilamiento):
    perfilamiento.respuestas[("POST", "/v1/originaciones")] = lambda r: httpx.Response(
        201, json={"id": "o-1", **json.loads(r.content), "pendiente": True}
    )


def test_el_socio_origina_el_credito_de_un_cliente_registrado(client, identidad, perfilamiento):
    _cliente_registrado(identidad)
    _perfilamiento_acepta(perfilamiento)

    respuesta = client.post("/v1/originaciones-hipotecarias", json=CUERPO)

    assert respuesta.status_code == 201
    assert respuesta.json() == {"estado": "pendiente", "valor": 180000000, "plazoMeses": 240}
    (busqueda,) = identidad.peticiones
    assert dict(busqueda.url.params) == {"tipo_documento": "CC", "numero_documento": "1012345678"}
    assert busqueda.headers["Authorization"] == "Bearer token-de-socio"
    (registro,) = perfilamiento.peticiones
    assert json.loads(registro.content) == {
        "cliente_id": USUARIO_ID,
        "valor": "180000000",
        "plazo_meses": 240,
        "origen": "socio",
    }


def test_socio_sin_alcance_de_originacion_es_403_y_no_llama_al_nucleo(app, identidad, perfilamiento):
    solo_catalogo = TestClient(app, headers=CABECERA_SOLO_CATALOGO)

    respuesta = solo_catalogo.post("/v1/originaciones-hipotecarias", json=CUERPO)

    assert respuesta.status_code == 403
    assert identidad.peticiones == []
    assert perfilamiento.peticiones == []


def test_documento_sin_cliente_es_404_y_no_registra_nada(client, identidad, perfilamiento):
    respuesta = client.post("/v1/originaciones-hipotecarias", json=CUERPO)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "cliente_no_registrado"
    assert perfilamiento.peticiones == []


def test_identidad_caida_es_503(client, identidad, perfilamiento):
    identidad.respuestas[("GET", "/v1/usuarios/documento")] = lambda _: httpx.Response(500)

    respuesta = client.post("/v1/originaciones-hipotecarias", json=CUERPO)

    assert respuesta.status_code == 503
    assert perfilamiento.peticiones == []


def test_identidad_que_rechaza_el_token_es_503(client, identidad, perfilamiento):
    identidad.respuestas[("GET", "/v1/usuarios/documento")] = lambda _: httpx.Response(403)

    assert client.post("/v1/originaciones-hipotecarias", json=CUERPO).status_code == 503


def test_perfilamiento_que_rechaza_los_valores_se_propaga(client, identidad, perfilamiento):
    _cliente_registrado(identidad)
    perfilamiento.respuestas[("POST", "/v1/originaciones")] = lambda _: httpx.Response(
        422, json={"codigo": "plazo_credito_invalido", "mensaje": "El plazo debe estar entre 1 y 480 meses"}
    )

    respuesta = client.post("/v1/originaciones-hipotecarias", json=CUERPO)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "plazo_credito_invalido"


@pytest.mark.parametrize(
    "cambio",
    [
        {"valor": 0},
        {"plazoMeses": 0},
        {"plazoMeses": 481},
        {"numeroDocumento": ""},
        {"tipoDocumento": ""},
        {"campoExtra": "x"},
    ],
)
def test_datos_invalidos_son_422_sin_llamar_al_nucleo(client, identidad, perfilamiento, cambio):
    respuesta = client.post("/v1/originaciones-hipotecarias", json={**CUERPO, **cambio})

    assert respuesta.status_code == 422
    assert identidad.peticiones == []
    assert perfilamiento.peticiones == []


def test_el_token_de_servicio_tiene_rol_socio_y_vence():
    ahora = datetime(2026, 11, 6, tzinfo=UTC)

    token = token_de_socio("secreto", "uid-socio", ahora)

    datos = jwt.decode(token, "secreto", algorithms=["HS256"], options={"verify_exp": False})
    assert {k: datos[k] for k in ("sub", "uid", "rol", "typ")} == {
        "sub": "api-socios",
        "uid": "uid-socio",
        "rol": "socio",
        "typ": "access",
    }
    assert datos["exp"] == int(ahora.timestamp()) + 300


def test_sin_secreto_no_se_firma_el_token():
    with pytest.raises(ValueError):
        token_de_socio("", "uid")


def _request_con_secreto(secreto: str = "secreto") -> SimpleNamespace:
    estado = SimpleNamespace(
        config=Settings(solventa_token_secret=secreto),
        http_ms_identidad=httpx.AsyncClient(base_url="http://ms-identidad"),
        http_ms_perfilamiento=httpx.AsyncClient(base_url="http://ms-perfilamiento"),
    )
    return SimpleNamespace(app=SimpleNamespace(state=estado), state=SimpleNamespace())


def test_las_dependencias_firman_el_token_con_el_socio_que_llama():
    request = _request_con_secreto()
    socio = Socio(socio_id=UUID(SOCIO_ID), nombre="Socio test", alcances=frozenset())

    identidad = obtener_cliente_identidad(request, socio)
    perfilamiento = obtener_cliente_perfilamiento(request, socio)

    for cliente in (identidad, perfilamiento):
        datos = jwt.decode(cliente._token, "secreto", algorithms=["HS256"])
        assert (datos["rol"], datos["uid"]) == ("socio", SOCIO_ID)
    assert perfilamiento._http is request.app.state.http_ms_perfilamiento


async def test_perfilamiento_recibe_el_token_de_socio():
    peticiones: list[httpx.Request] = []

    def responder(request: httpx.Request) -> httpx.Response:
        peticiones.append(request)
        return httpx.Response(201, json={"id": "o-1"})

    http = httpx.AsyncClient(transport=httpx.MockTransport(responder), base_url="http://ms-perfilamiento")
    cliente = ClienteMsPerfilamiento(http, "corr", "token-de-socio")

    await cliente.registrar_originacion(USUARIO_ID, 180000000, 240)

    assert peticiones[0].headers["Authorization"] == "Bearer token-de-socio"


def test_sin_api_key_es_401_aunque_falte_el_secreto_de_servicio(nucleo, identidad, perfilamiento):
    app = crear_app(Settings(socios=REGISTRO_SOCIOS))

    respuesta = TestClient(app).post("/v1/originaciones-hipotecarias", json=CUERPO)

    assert respuesta.status_code == 401
