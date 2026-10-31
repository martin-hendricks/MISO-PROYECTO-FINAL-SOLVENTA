from datetime import datetime

import httpx
import jwt
import pytest

from app.routers.registro import POLITICA_VERSION, TIPO_DOCUMENTO_DEFECTO

BODY = {
    "nombre": "Camila",
    "apellidos": "Restrepo",
    "documento": "1012345678",
    "correo": "camila@correo.com",
    "contrasena": "secreto123",
    "habeasData": True,
}


def test_alta_web(client):
    response = client.post("/v1/registro", json=BODY)
    assert response.status_code == 200
    data = response.json()
    assert data["cliente"]["correo"] == "camila@correo.com"
    assert "pruebaDeVida" not in data
    assert "contrasena" not in data["cliente"]


def test_alta_abre_sesion_de_cliente(client):
    data = client.post("/v1/registro", json=BODY).json()
    claims = jwt.decode(data["accessToken"], "test-secret", algorithms=["HS256"])
    assert claims["sub"] == "camila@correo.com"
    assert claims["rol"] == "cliente"
    assert data["refreshToken"]
    assert data["expiraEn"] == 900


def test_alta_deja_marca_de_consentimiento_auditable(client):
    marca = client.post("/v1/registro", json=BODY).json()["consentimiento"]
    assert marca["habeasData"] is True
    assert marca["version"] == POLITICA_VERSION
    assert datetime.fromisoformat(marca["otorgadoEn"]).tzinfo is not None


def test_alta_sin_consentimiento_se_rechaza(client):
    response = client.post("/v1/registro", json={**BODY, "habeasData": False})
    assert response.status_code == 422


@pytest.mark.parametrize("campo", ["contrasena", "habeasData"])
def test_alta_incompleta_se_rechaza(client, campo):
    body = {key: value for key, value in BODY.items() if key != campo}
    assert client.post("/v1/registro", json=body).status_code == 422


def test_alta_envia_documento_y_correo_a_ms_identidad(client, nucleo_identidad):
    client.post("/v1/registro", json=BODY)

    peticion = nucleo_identidad.peticiones[-1]
    assert (peticion.method, peticion.url.path) == ("POST", "/v1/usuarios")
    cuerpo = peticion.read()
    assert BODY["documento"].encode() in cuerpo
    assert BODY["correo"].encode() in cuerpo
    assert TIPO_DOCUMENTO_DEFECTO.encode() in cuerpo


def test_alta_con_cuenta_ya_existente_en_ms_identidad_es_409(client, nucleo_identidad):
    nucleo_identidad.respuestas[("POST", "/v1/usuarios")] = lambda request: httpx.Response(
        409, json={"codigo": "cuenta_duplicada", "mensaje": "La cuenta ya existe"}
    )

    response = client.post("/v1/registro", json=BODY)

    assert response.status_code == 409


def test_alta_con_identidad_rechazada_por_kyc_es_422_y_no_cuenta_duplicada(client, nucleo_identidad):
    nucleo_identidad.respuestas[("POST", "/v1/usuarios")] = lambda request: httpx.Response(
        422, json={"codigo": "identidad_no_verificada", "mensaje": "No fue posible verificar la identidad"}
    )

    response = client.post("/v1/registro", json=BODY)

    assert response.status_code == 422
    assert response.json()["detail"] == "No fue posible verificar la identidad"


def test_alta_con_kyc_caido_en_ms_identidad_no_esta_disponible(client, nucleo_identidad):
    nucleo_identidad.respuestas[("POST", "/v1/usuarios")] = lambda request: httpx.Response(
        503, json={"codigo": "dependencia_no_disponible", "mensaje": "No fue posible consultar el verificador KYC"}
    )

    response = client.post("/v1/registro", json=BODY)

    assert response.status_code == 503
