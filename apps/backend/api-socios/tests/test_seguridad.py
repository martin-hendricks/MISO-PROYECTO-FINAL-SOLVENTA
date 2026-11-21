import hashlib
import json
from types import SimpleNamespace
from uuid import UUID

import httpx
import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.clients.base import ServicioNoDisponible
from app.registro_socios import RegistroSociosIdentidad
from app.seguridad import Socio, exigir_alcance, exigir_api_key_socio

from .conftest import RegistroSociosEnMemoria

API_KEY = "clave-test-socio"
SOCIO_ID = "6f1c2a4e-0000-4000-8000-000000000001"
SECRETO = "secreto-de-prueba"
RUTA = ("POST", "/v1/socios/resolucion")


def _huella(clave: str) -> str:
    return hashlib.sha256(clave.encode()).hexdigest()


def _socio(alcances=("catalogo:leer",)) -> Socio:
    return Socio(
        socio_id=UUID(SOCIO_ID), nombre="Socio 1", alcances=frozenset(alcances)
    )


def _request(socios: dict[str, Socio]) -> SimpleNamespace:
    registro = RegistroSociosEnMemoria(socios)
    return SimpleNamespace(
        app=SimpleNamespace(state=SimpleNamespace(registro_socios=registro))
    )


async def test_sin_cabecera_responde_401_sin_consultar_el_registro():
    request = _request({_huella(API_KEY): _socio()})

    with pytest.raises(HTTPException) as exc:
        await exigir_api_key_socio(request, None)

    assert exc.value.status_code == 401
    assert request.app.state.registro_socios.consultas == []


async def test_api_key_invalida_responde_401():
    with pytest.raises(HTTPException) as exc:
        await exigir_api_key_socio(
            _request({_huella(API_KEY): _socio()}), "clave-que-no-existe"
        )

    assert exc.value.status_code == 401


async def test_api_key_valida_resuelve_el_socio_por_su_huella():
    request = _request({_huella(API_KEY): _socio()})

    socio = await exigir_api_key_socio(request, API_KEY)

    assert socio == _socio()
    assert request.app.state.registro_socios.consultas == [_huella(API_KEY)]


async def test_la_huella_enviada_como_clave_no_sirve():
    with pytest.raises(HTTPException) as exc:
        await exigir_api_key_socio(
            _request({_huella(API_KEY): _socio()}), _huella(API_KEY)
        )

    assert exc.value.status_code == 401


async def test_socio_sin_el_alcance_responde_403():
    socio = await exigir_api_key_socio(_request({_huella(API_KEY): _socio()}), API_KEY)

    with pytest.raises(HTTPException) as exc:
        exigir_alcance("originaciones:escribir")(socio)

    assert exc.value.status_code == 403


async def test_socio_con_el_alcance_pasa():
    socio = await exigir_api_key_socio(_request({_huella(API_KEY): _socio()}), API_KEY)

    assert exigir_alcance("catalogo:leer")(socio) is socio


class _Identidad:
    def __init__(self, respuesta) -> None:
        self.respuesta = respuesta
        self.peticiones: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.peticiones.append(request)
        return self.respuesta(request)


def _registro(
    identidad: _Identidad, reloj=lambda: 0.0, ttl_s: float = 30.0
) -> RegistroSociosIdentidad:
    http = httpx.AsyncClient(
        transport=httpx.MockTransport(identidad), base_url="http://ms-identidad"
    )
    return RegistroSociosIdentidad(http, SECRETO, ttl_s, reloj)


def _responde_socio(_: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"socio_id": SOCIO_ID, "nombre": "Socio 1", "alcances": ["catalogo:leer"]},
    )


async def test_resuelve_el_socio_en_ms_identidad_con_token_de_servicio_y_sin_la_clave():
    identidad = _Identidad(_responde_socio)

    socio = await _registro(identidad).resolver(_huella(API_KEY))

    assert socio == _socio()
    [peticion] = identidad.peticiones
    assert (peticion.method, peticion.url.path) == RUTA
    assert json.loads(peticion.content) == {"huella_sha256": _huella(API_KEY)}
    assert API_KEY not in peticion.content.decode()
    token = peticion.headers["Authorization"].removeprefix("Bearer ")
    claims = jwt.decode(token, SECRETO, algorithms=["HS256"])
    assert claims["rol"] == "socio"
    assert claims["sub"] == "api-socios"
    assert claims["typ"] == "access"
    assert UUID(claims["uid"])


async def test_huella_desconocida_o_revocada_es_none():
    identidad = _Identidad(
        lambda _: httpx.Response(404, json={"codigo": "no_encontrado"})
    )

    assert await _registro(identidad).resolver(_huella(API_KEY)) is None


@pytest.mark.parametrize(
    "respuesta",
    [
        lambda _: httpx.Response(500),
        lambda _: httpx.Response(401),
        lambda request: (_ for _ in ()).throw(
            httpx.ConnectError("caido", request=request)
        ),
    ],
)
async def test_ms_identidad_caido_es_servicio_no_disponible(respuesta):
    with pytest.raises(ServicioNoDisponible):
        await _registro(_Identidad(respuesta)).resolver(_huella(API_KEY))


async def test_cachea_el_socio_resuelto_durante_el_ttl():
    identidad = _Identidad(_responde_socio)
    ahora = [0.0]
    registro = _registro(identidad, reloj=lambda: ahora[0], ttl_s=30.0)

    await registro.resolver(_huella(API_KEY))
    ahora[0] = 29.0
    await registro.resolver(_huella(API_KEY))

    assert len(identidad.peticiones) == 1


async def test_vuelve_a_consultar_al_vencer_el_ttl_y_toma_la_revocacion():
    respuestas = iter(
        [
            _responde_socio,
            lambda _: httpx.Response(404, json={"codigo": "no_encontrado"}),
        ]
    )
    identidad = _Identidad(lambda request: next(respuestas)(request))
    ahora = [0.0]
    registro = _registro(identidad, reloj=lambda: ahora[0], ttl_s=30.0)

    assert await registro.resolver(_huella(API_KEY)) == _socio()
    ahora[0] = 31.0

    assert await registro.resolver(_huella(API_KEY)) is None
    assert len(identidad.peticiones) == 2


async def test_no_cachea_las_huellas_desconocidas():
    respuestas = iter(
        [
            lambda _: httpx.Response(404, json={"codigo": "no_encontrado"}),
            _responde_socio,
        ]
    )
    identidad = _Identidad(lambda request: next(respuestas)(request))
    registro = _registro(identidad)

    assert await registro.resolver(_huella(API_KEY)) is None
    assert await registro.resolver(_huella(API_KEY)) == _socio()


def test_ms_identidad_caido_responde_503_y_no_401(app):
    class _Caido:
        async def resolver(self, huella_sha256: str):
            raise ServicioNoDisponible("ms-identidad")

    app.state.registro_socios = _Caido()

    respuesta = TestClient(app, headers={"X-Socio-Api-Key": API_KEY}).get(
        "/v1/catalogo"
    )

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "servicio_no_disponible"


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"nombre": "Socio 1", "alcances": []},
        {"socio_id": "no-es-uuid", "nombre": "x", "alcances": []},
        None,
        [],
    ],
)
async def test_respuesta_malformada_de_ms_identidad_es_servicio_no_disponible(cuerpo):
    identidad = _Identidad(lambda _: httpx.Response(200, json=cuerpo))

    with pytest.raises(ServicioNoDisponible):
        await _registro(identidad).resolver(_huella(API_KEY))
