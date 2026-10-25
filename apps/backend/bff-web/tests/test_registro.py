from datetime import datetime

import jwt
import pytest

from app.routers.registro import POLITICA_VERSION

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
