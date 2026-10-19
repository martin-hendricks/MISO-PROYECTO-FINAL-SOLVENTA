from tests.conftest import customer_token, desk_token


def test_ingreso_sin_rol(client):
    response = client.post(
        "/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["expiraEn"] == 900
    assert "rol" not in body


def test_rol_enviado_despues_se_ignora(client):
    headers = {"Authorization": f"Bearer {customer_token(client)}"}
    response = client.post(
        "/cliente/cotizaciones",
        headers=headers,
        json={"ramo": "Protección de dispositivo", "datosRiesgo": {}, "rol": "operador"},
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "oferta_vigente"


def test_token_de_escritorio_es_403(client):
    for rol in ("asesor", "operador"):
        headers = {"Authorization": f"Bearer {desk_token(rol)}"}
        assert client.get("/cliente/inicio", headers=headers).status_code == 403


def test_sin_token_es_401(client):
    assert client.get("/cliente/inicio").status_code == 401
