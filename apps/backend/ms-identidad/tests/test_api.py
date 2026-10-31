from app.dependencies import obtener_verificador_kyc
from app.infrastructure.kyc import VerificadorKYCStub

BODY_ALTA = {
    "tipo_documento": "CC",
    "numero_documento": "1012345678",
    "email": "camila@correo.com",
    "password": "clave-secreta-123",
}


def _crear(client, **overrides):
    return client.post("/v1/usuarios", json={**BODY_ALTA, **overrides})


def test_alta_devuelve_201_con_el_usuario_sin_password(client):
    respuesta = _crear(client)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["email"] == "camila@correo.com"
    assert cuerpo["tipo_documento"] == "CC"
    assert cuerpo["estado"] == "ACTIVO"
    assert "password" not in cuerpo
    assert "password_hash" not in cuerpo


def test_alta_con_email_duplicado_es_409(client):
    _crear(client)

    respuesta = _crear(client, numero_documento="otro-documento")

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "cuenta_duplicada"


def test_alta_con_documento_duplicado_es_409(client):
    _crear(client)

    respuesta = _crear(client, email="otro@correo.com")

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "cuenta_duplicada"


def test_alta_con_documento_rechazado_por_kyc_es_422(client):
    client.app.dependency_overrides[obtener_verificador_kyc] = lambda: VerificadorKYCStub(
        documentos_rechazados=["0000000000"]
    )

    respuesta = _crear(client, numero_documento="0000000000")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "identidad_no_verificada"


def test_alta_con_kyc_caido_es_503(client):
    client.app.dependency_overrides[obtener_verificador_kyc] = lambda: VerificadorKYCStub(fallar=True)

    respuesta = _crear(client)

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "dependencia_no_disponible"


def test_alta_con_password_corto_es_422(client):
    respuesta = _crear(client, password="1234567")

    assert respuesta.status_code == 422


def test_alta_sin_email_es_422(client):
    respuesta = client.post(
        "/v1/usuarios",
        json={k: v for k, v in BODY_ALTA.items() if k != "email"},
    )

    assert respuesta.status_code == 422


def test_autenticacion_con_credenciales_correctas_es_200(client):
    _crear(client)

    respuesta = client.post(
        "/v1/usuarios/autenticacion",
        json={"email": "camila@correo.com", "password": "clave-secreta-123"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == "camila@correo.com"


def test_autenticacion_con_password_incorrecto_es_401(client):
    _crear(client)

    respuesta = client.post(
        "/v1/usuarios/autenticacion",
        json={"email": "camila@correo.com", "password": "clave-incorrecta"},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "credenciales_invalidas"


def test_autenticacion_con_email_inexistente_es_401_con_el_mismo_codigo(client):
    respuesta = client.post(
        "/v1/usuarios/autenticacion",
        json={"email": "nadie@correo.com", "password": "clave-secreta-123"},
    )

    assert respuesta.status_code == 401
    assert respuesta.json()["codigo"] == "credenciales_invalidas"


def test_autenticacion_es_insensible_a_mayusculas_en_el_email(client):
    _crear(client)

    respuesta = client.post(
        "/v1/usuarios/autenticacion",
        json={"email": "CAMILA@CORREO.com", "password": "clave-secreta-123"},
    )

    assert respuesta.status_code == 200


def test_health_ready_sin_base_de_datos_devuelve_503(client):
    # El cliente de pruebas crea la app real (lifespan real -> motor SQLAlchemy real)
    # pero sin un Postgres escuchando en DATABASE_URL: el ping debe fallar controladamente.
    respuesta = client.get("/health/ready")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable"}


def test_health_live_no_toca_la_base_de_datos(client):
    assert client.get("/health/live").json() == {"status": "ok"}
