import json

import httpx
import pytest

from tests.conftest import token

SOCIO = "33333333-3333-4333-8333-333333333333"
CREDENCIAL = "44444444-4444-4444-8444-444444444444"


def _auth(client, rol="operador"):
    return {"Authorization": f"Bearer {token(client, rol)}"}


def _socio(**cambios) -> dict:
    base = {
        "socio_id": SOCIO,
        "nombre": "Aliado",
        "alcances": ["catalogo:leer", "cotizaciones:escribir"],
        "estado": "ACTIVO",
        "creado_en": "2026-11-20T10:00:00Z",
        "credenciales": [
            {
                "credencial_id": CREDENCIAL,
                "creada_en": "2026-11-20T10:00:00Z",
                "revocada_en": None,
            }
        ],
    }
    base.update(cambios)
    return base


def _vista(**cambios) -> dict:
    base = {
        "socioId": SOCIO,
        "nombre": "Aliado",
        "alcances": ["catalogo:leer", "cotizaciones:escribir"],
        "estado": "ACTIVO",
        "creadoEn": "2026-11-20T10:00:00Z",
        "credenciales": [
            {
                "credencialId": CREDENCIAL,
                "creadaEn": "2026-11-20T10:00:00Z",
                "revocadaEn": None,
            }
        ],
    }
    base.update(cambios)
    return base


@pytest.mark.parametrize("rol", ["asesor", "operador"])
def test_listar_traduce_a_camel_para_asesor_y_operador(client, nucleo_identidad, rol):
    nucleo_identidad.respuestas[("GET", "/v1/socios")] = lambda _: httpx.Response(
        200, json={"socios": [_socio()]}
    )
    cabeceras = _auth(client, rol)

    respuesta = client.get("/v1/backoffice/socios", headers=cabeceras)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"socios": [_vista()]}
    peticion = nucleo_identidad.peticiones[-1]
    assert (peticion.method, peticion.url.path) == ("GET", "/v1/socios")
    assert peticion.headers["Authorization"] == cabeceras["Authorization"]


def test_crear_reenvia_nombre_y_alcances_y_devuelve_api_key(client, nucleo_identidad):
    nucleo_identidad.respuestas[("POST", "/v1/socios")] = lambda _: httpx.Response(
        201,
        json={
            "socio_id": SOCIO,
            "nombre": "Aliado",
            "alcances": ["catalogo:leer"],
            "estado": "ACTIVO",
            "creado_en": "2026-11-20T10:00:00Z",
            "credencial_id": CREDENCIAL,
            "api_key": "sk_live_abc",
        },
    )
    cabeceras = _auth(client)

    respuesta = client.post(
        "/v1/backoffice/socios",
        headers=cabeceras,
        json={"nombre": "Aliado", "alcances": ["catalogo:leer"]},
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "socioId": SOCIO,
        "nombre": "Aliado",
        "alcances": ["catalogo:leer"],
        "estado": "ACTIVO",
        "creadoEn": "2026-11-20T10:00:00Z",
        "credencialId": CREDENCIAL,
        "apiKey": "sk_live_abc",
    }
    peticion = nucleo_identidad.peticiones[-1]
    assert (peticion.method, peticion.url.path) == ("POST", "/v1/socios")
    assert json.loads(peticion.content) == {
        "nombre": "Aliado",
        "alcances": ["catalogo:leer"],
    }
    assert peticion.headers["Authorization"] == cabeceras["Authorization"]


@pytest.mark.parametrize(
    "cuerpo",
    [
        {"nombre": "", "alcances": ["catalogo:leer"]},
        {"nombre": "Aliado", "alcances": []},
        {"nombre": "Aliado", "alcances": ["polizas:borrar"]},
        {"nombre": "Aliado", "alcances": ["catalogo:leer"], "extra": True},
    ],
)
def test_crear_con_cuerpo_invalido_responde_422_sin_llamar_a_identidad(
    client, nucleo_identidad, cuerpo
):
    cabeceras = _auth(client)
    antes = len(nucleo_identidad.peticiones)

    respuesta = client.post("/v1/backoffice/socios", headers=cabeceras, json=cuerpo)

    assert respuesta.status_code == 422
    assert len(nucleo_identidad.peticiones) == antes


def test_rotar_devuelve_nueva_credencial(client, nucleo_identidad):
    ruta = f"/v1/socios/{SOCIO}/credenciales"
    nucleo_identidad.respuestas[("POST", ruta)] = lambda _: httpx.Response(
        201, json={"credencial_id": CREDENCIAL, "api_key": "sk_live_nueva"}
    )
    cabeceras = _auth(client, "asesor")

    respuesta = client.post(
        f"/v1/backoffice/socios/{SOCIO}/credenciales", headers=cabeceras
    )

    assert respuesta.status_code == 201
    assert respuesta.json() == {"credencialId": CREDENCIAL, "apiKey": "sk_live_nueva"}
    peticion = nucleo_identidad.peticiones[-1]
    assert (peticion.method, peticion.url.path) == ("POST", ruta)
    assert peticion.headers["Authorization"] == cabeceras["Authorization"]


def test_rotar_socio_revocado_propaga_409(client, nucleo_identidad):
    nucleo_identidad.respuestas[("POST", f"/v1/socios/{SOCIO}/credenciales")] = (
        lambda _: httpx.Response(
            409, json={"codigo": "socio_revocado", "mensaje": "El socio está revocado"}
        )
    )

    respuesta = client.post(
        f"/v1/backoffice/socios/{SOCIO}/credenciales", headers=_auth(client)
    )

    assert respuesta.status_code == 409
    assert respuesta.json() == {
        "codigo": "socio_revocado",
        "mensaje": "El socio está revocado",
    }


def test_revocar_credencial_responde_204_sin_cuerpo(client, nucleo_identidad):
    ruta = f"/v1/socios/{SOCIO}/credenciales/{CREDENCIAL}"
    nucleo_identidad.respuestas[("DELETE", ruta)] = lambda _: httpx.Response(204)
    cabeceras = _auth(client)

    respuesta = client.delete(
        f"/v1/backoffice/socios/{SOCIO}/credenciales/{CREDENCIAL}", headers=cabeceras
    )

    assert respuesta.status_code == 204
    assert respuesta.content == b""
    peticion = nucleo_identidad.peticiones[-1]
    assert (peticion.method, peticion.url.path) == ("DELETE", ruta)
    assert peticion.headers["Authorization"] == cabeceras["Authorization"]


def test_revocar_credencial_inexistente_responde_404(client, nucleo_identidad):
    respuesta = client.delete(
        f"/v1/backoffice/socios/{SOCIO}/credenciales/{CREDENCIAL}",
        headers=_auth(client),
    )

    assert respuesta.status_code == 404
    assert respuesta.json() == {"codigo": "no_encontrado", "mensaje": "No existe"}


def test_revocar_socio_devuelve_vista_camel(client, nucleo_identidad):
    ruta = f"/v1/socios/{SOCIO}/revocacion"
    revocado = _socio(
        estado="REVOCADO",
        credenciales=[
            {
                "credencial_id": CREDENCIAL,
                "creada_en": "2026-11-20T10:00:00Z",
                "revocada_en": "2026-11-20T11:00:00Z",
            }
        ],
    )
    nucleo_identidad.respuestas[("POST", ruta)] = lambda _: httpx.Response(
        200, json=revocado
    )
    cabeceras = _auth(client)

    respuesta = client.post(
        f"/v1/backoffice/socios/{SOCIO}/revocacion", headers=cabeceras
    )

    assert respuesta.status_code == 200
    assert respuesta.json() == _vista(
        estado="REVOCADO",
        credenciales=[
            {
                "credencialId": CREDENCIAL,
                "creadaEn": "2026-11-20T10:00:00Z",
                "revocadaEn": "2026-11-20T11:00:00Z",
            }
        ],
    )
    peticion = nucleo_identidad.peticiones[-1]
    assert (peticion.method, peticion.url.path) == ("POST", ruta)
    assert peticion.headers["Authorization"] == cabeceras["Authorization"]


RUTAS = [
    ("GET", "/v1/backoffice/socios", None),
    (
        "POST",
        "/v1/backoffice/socios",
        {"nombre": "Aliado", "alcances": ["catalogo:leer"]},
    ),
    ("POST", f"/v1/backoffice/socios/{SOCIO}/credenciales", None),
    ("DELETE", f"/v1/backoffice/socios/{SOCIO}/credenciales/{CREDENCIAL}", None),
    ("POST", f"/v1/backoffice/socios/{SOCIO}/revocacion", None),
]


@pytest.mark.parametrize(("metodo", "ruta", "cuerpo"), RUTAS)
def test_rol_cliente_recibe_403_sin_llamar_a_identidad(
    client, nucleo_identidad, metodo, ruta, cuerpo
):
    cabeceras = _auth(client, "cliente")
    antes = len(nucleo_identidad.peticiones)

    respuesta = client.request(metodo, ruta, headers=cabeceras, json=cuerpo)

    assert respuesta.status_code == 403
    assert len(nucleo_identidad.peticiones) == antes


@pytest.mark.parametrize(("metodo", "ruta", "cuerpo"), RUTAS)
def test_sin_token_responde_401(client, nucleo_identidad, metodo, ruta, cuerpo):
    respuesta = client.request(metodo, ruta, json=cuerpo)

    assert respuesta.status_code == 401
    assert nucleo_identidad.peticiones == []
