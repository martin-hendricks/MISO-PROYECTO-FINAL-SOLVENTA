def test_ingreso_asesor_devuelve_par_de_tokens(client):
    response = client.post(
        "/sesion/ingreso",
        json={"correo": "asesor@solventa.com", "contrasena": "secreto", "rol": "asesor"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["expiraEn"] == 900
    assert body["accessToken"]
    assert body["refreshToken"]


def test_rol_fuera_de_lista_es_400(client):
    response = client.post(
        "/sesion/ingreso",
        json={"correo": "asesor@solventa.com", "contrasena": "secreto", "rol": "admin"},
    )
    assert response.status_code == 400


def test_refresh_rota_el_par(client):
    ingreso = client.post(
        "/sesion/ingreso",
        json={"correo": "c@solventa.com", "contrasena": "secreto", "rol": "cliente"},
    )
    response = client.post("/sesion/refresh", json={"refreshToken": ingreso.json()["refreshToken"]})
    assert response.status_code == 200
    assert response.json()["expiraEn"] == 900


def test_salida_exige_token(client):
    assert client.post("/sesion/salida").status_code == 401


def test_salida_acepta_cualquier_rol_valido(client):
    from tests.conftest import token

    headers = {"Authorization": f"Bearer {token(client, 'operador')}"}
    assert client.post("/sesion/salida", headers=headers).status_code == 200
