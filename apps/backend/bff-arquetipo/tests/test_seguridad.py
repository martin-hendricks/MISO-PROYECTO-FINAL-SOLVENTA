from fastapi.testclient import TestClient

from app.config import Settings
from app.main import crear_app

from .conftest import EJEMPLO, EMISOR, auth


def _rutas_de_negocio(app):
    for ruta, operaciones in app.openapi()["paths"].items():
        if ruta.startswith("/v1"):
            for metodo in operaciones:
                yield metodo.upper(), ruta.replace("{ejemplo_id}", EJEMPLO["id"])


def test_ninguna_ruta_v1_responde_sin_token(app, client, nucleo):
    rutas = list(_rutas_de_negocio(app))
    assert rutas, "el BFF debe exponer rutas /v1"
    for metodo, ruta in rutas:
        respuesta = client.request(metodo, ruta)
        assert respuesta.status_code == 401, f"{metodo} {ruta} quedó accesible sin token"
    assert nucleo.peticiones == [], "una petición sin token no debe alcanzar el núcleo"


def test_token_expirado_no_alcanza_el_nucleo(client, nucleo):
    expirado = EMISOR.emitir(expira_en=-120)
    respuesta = client.get("/v1/inicio", headers={"Authorization": f"Bearer {expirado}"})

    assert respuesta.status_code == 401
    assert nucleo.peticiones == []


def test_sin_llave_publica_falla_cerrado():
    client = TestClient(crear_app(Settings(jwt_public_key="")))
    assert client.get("/v1/inicio", headers=auth()).status_code == 503


def test_health_es_publico(client):
    assert client.get("/health").status_code == 200
