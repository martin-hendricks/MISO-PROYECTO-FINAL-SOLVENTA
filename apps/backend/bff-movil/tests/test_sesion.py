from tests.conftest import customer_token, desk_token


def _ingreso(client):
    response = client.post(
        "/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    )
    assert response.status_code == 200
    return response.json()


def test_salida_revoca_el_refresh_token(client):
    """El hueco real: antes de esto, el logout no invalidaba nada del lado
    servidor y un refresh token robado seguia sirviendo para generar pares
    nuevos indefinidamente hasta su expiracion natural."""
    par = _ingreso(client)
    headers = {"Authorization": f"Bearer {par['accessToken']}"}

    salida = client.post("/sesion/salida", headers=headers, json={"refreshToken": par["refreshToken"]})
    assert salida.status_code == 200

    refrescado = client.post("/sesion/refresh", json={"refreshToken": par["refreshToken"]})
    assert refrescado.status_code == 401


def test_salida_revoca_el_access_token(client):
    """Un access token revocado no debe servir en ningun endpoint protegido
    despues del logout."""
    par = _ingreso(client)
    headers = {"Authorization": f"Bearer {par['accessToken']}"}

    assert client.post("/sesion/salida", headers=headers).status_code == 200
    assert client.get("/cliente/inicio", headers=headers).status_code == 401


def test_tokens_no_revocados_siguen_funcionando(client):
    """Revocar la sesion de un usuario no debe afectar a otro par de tokens
    valido y no revocado."""
    par = _ingreso(client)

    otro = _ingreso(client)
    client.post(
        "/sesion/salida",
        headers={"Authorization": f"Bearer {otro['accessToken']}"},
        json={"refreshToken": otro["refreshToken"]},
    )

    headers = {"Authorization": f"Bearer {par['accessToken']}"}
    assert client.post("/sesion/salida", headers=headers).status_code == 200
    refrescado = client.post("/sesion/refresh", json={"refreshToken": par["refreshToken"]})
    assert refrescado.status_code == 200


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
