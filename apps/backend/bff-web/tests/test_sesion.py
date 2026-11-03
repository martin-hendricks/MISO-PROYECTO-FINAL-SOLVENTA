def test_ingreso_asesor_devuelve_par_de_tokens(client):
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "asesor@solventa.com", "contrasena": "secreto", "rol": "asesor"},
    )
    body = response.json()
    assert response.status_code == 200
    assert body["expiraEn"] == 900
    assert body["accessToken"]
    assert body["refreshToken"]


def test_rol_fuera_de_lista_es_400(client):
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "asesor@solventa.com", "contrasena": "secreto", "rol": "admin"},
    )
    assert response.status_code == 400


def test_credenciales_rechazadas_por_ms_identidad_son_401_sin_tokens(client, nucleo_identidad):
    import httpx

    nucleo_identidad.respuestas[("POST", "/v1/usuarios/autenticacion")] = lambda request: httpx.Response(
        401, json={"codigo": "credenciales_invalidas", "mensaje": "Correo o contraseña incorrectos"}
    )

    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "incorrecta", "rol": "cliente"},
    )
    assert response.status_code == 401
    assert "accessToken" not in response.json()


def test_ingreso_envia_correo_y_contrasena_a_ms_identidad(client, nucleo_identidad):
    client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "clave-secreta-123", "rol": "cliente"},
    )

    peticion = nucleo_identidad.peticiones[-1]
    assert (peticion.method, peticion.url.path) == ("POST", "/v1/usuarios/autenticacion")
    cuerpo = peticion.read()
    assert b"camila@correo.com" in cuerpo
    assert b"clave-secreta-123" in cuerpo


def test_refresh_rota_el_par(client):
    ingreso = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "c@correo.com", "contrasena": "secreto", "rol": "cliente"},
    )
    response = client.post("/v1/sesion/refresh", json={"refreshToken": ingreso.json()["refreshToken"]})
    assert response.status_code == 200
    assert response.json()["expiraEn"] == 900


def test_salida_exige_token(client):
    assert client.post("/v1/sesion/salida").status_code == 401


def test_salida_acepta_cualquier_rol_valido(client):
    from tests.conftest import token

    headers = {"Authorization": f"Bearer {token(client, 'operador')}"}
    assert client.post("/v1/sesion/salida", headers=headers).status_code == 200


def test_sin_rol_el_bff_asigna_asesor(client):
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila.restrepo@solventa.co", "contrasena": "secreto"},
    )
    headers = {"Authorization": f"Bearer {response.json()['accessToken']}"}
    assert response.status_code == 200
    assert client.get("/v1/asesor/clientes", headers=headers).status_code == 200
    assert client.get("/v1/operador/avisos", headers=headers).status_code == 403


def test_sin_rol_la_cuenta_de_operador_entra_como_operador(client):
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "Operador.bogota@solventa.co", "contrasena": "secreto"},
    )
    headers = {"Authorization": f"Bearer {response.json()['accessToken']}"}
    assert client.get("/v1/operador/avisos", headers=headers).status_code == 200
    assert client.get("/v1/asesor/clientes", headers=headers).status_code == 403


def test_cuenta_corporativa_pidiendo_rol_cliente_es_401(client):
    """Bug real: /login (canal cliente) manda rol="cliente" fijo sin
    importar el correo que se escriba ahi. Antes de este chequeo, una
    cuenta de asesor/operador (dominio @solventa.co/.com) podia loguearse
    por /login y quedar con un JWT valido de rol "cliente" -- la identidad
    era real (ms-identidad la confirmaba), pero el rol no tenia ninguna
    relacion con la cuenta real."""
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "asesor@solventa.co", "contrasena": "secreto", "rol": "cliente"},
    )
    assert response.status_code == 401
    assert "accessToken" not in response.json()


def test_cliente_pidiendo_rol_corporativo_es_401(client):
    """Simetrico al caso anterior: un correo que no es de dominio
    corporativo no puede entrar al back-office pidiendo rol=asesor/operador."""
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto", "rol": "asesor"},
    )
    assert response.status_code == 401
    assert "accessToken" not in response.json()


def test_sin_rol_una_cuenta_no_corporativa_entra_como_cliente(client):
    """Complementa test_sin_rol_el_bff_asigna_asesor: sin rol explicito,
    _rol_asignado ya no se aplica a cualquier correo -- solo a dominios
    corporativos. Un correo normal sin rol explicito (nunca deberia pasar
    desde /login real, que siempre manda rol="cliente", pero cubre el
    default) cae en "cliente", no en "asesor"."""
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    )
    headers = {"Authorization": f"Bearer {response.json()['accessToken']}"}
    assert response.status_code == 200
    assert client.get("/v1/asesor/clientes", headers=headers).status_code == 403
