from uuid import uuid4

import pytest

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


def test_alta_con_canal_lo_persiste(client):
    respuesta = _crear(client, canal="android")

    assert respuesta.status_code == 201
    assert respuesta.json()["canal"] == "android"


def test_alta_sin_canal_queda_nulo(client):
    respuesta = _crear(client)

    assert respuesta.status_code == 201
    assert respuesta.json()["canal"] is None


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


def test_consultar_y_actualizar_perfil(client):
    from tests.conftest import token_de

    creado = _crear(client, nombre="Camila", apellidos="Restrepo").json()
    usuario_id = creado["usuario_id"]
    propio = {"Authorization": f"Bearer {token_de(usuario_id, 'cliente')}"}

    consulta = client.get(f"/v1/usuarios/{usuario_id}", headers=propio)
    assert consulta.status_code == 200
    assert consulta.json()["nombre"] == "Camila"

    perfil = client.patch(
        f"/v1/usuarios/{usuario_id}/perfil",
        json={"nombre": "Ana", "apellidos": "Lopez"},
        headers=propio,
    )
    assert perfil.status_code == 200
    assert perfil.json()["apellidos"] == "Lopez"
    assert perfil.json()["rol"] == "cliente"
    assert client.get(f"/v1/usuarios/{usuario_id}", headers=propio).json()["nombre"] == "Ana"

    ajeno = {"Authorization": f"Bearer {token_de(str(uuid4()), 'cliente')}"}
    assert client.get(f"/v1/usuarios/{usuario_id}", headers=ajeno).status_code == 404
    assert client.get(f"/v1/usuarios/{uuid4()}").status_code == 404
    assert (
        client.patch(
            f"/v1/usuarios/{uuid4()}/perfil", json={"nombre": "Ana", "apellidos": "Lopez"}
        ).status_code
        == 404
    )


def test_health_ready_sin_base_de_datos_devuelve_503(client):
    # El cliente de pruebas crea la app real (lifespan real -> motor SQLAlchemy real)
    # pero sin un Postgres escuchando en DATABASE_URL: el ping debe fallar controladamente.
    respuesta = client.get("/health/ready")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable"}


def test_health_live_no_toca_la_base_de_datos(client):
    assert client.get("/health/live").json() == {"status": "ok"}


def _buscar(client, rol: str, tipo: str = "CC", numero: str = "1012345678"):
    from tests.conftest import token_de

    return client.get(
        "/v1/usuarios/documento",
        params={"tipo_documento": tipo, "numero_documento": numero},
        headers={"Authorization": f"Bearer {token_de(str(uuid4()), rol)}"},
    )


@pytest.mark.parametrize("rol", ["socio", "asesor", "operador"])
def test_buscar_por_documento_devuelve_solo_el_usuario_id(client, rol):
    creado = _crear(client).json()

    respuesta = _buscar(client, rol)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"usuario_id": creado["usuario_id"]}


def test_buscar_por_documento_normaliza_como_el_alta(client):
    creado = _crear(client).json()

    respuesta = _buscar(client, "socio", tipo=" cc ", numero=" 1012345678 ")

    assert respuesta.json() == {"usuario_id": creado["usuario_id"]}


def test_buscar_por_documento_inexistente_es_404(client):
    assert _buscar(client, "socio", numero="999").status_code == 404


def test_un_cliente_no_puede_buscar_por_documento(client):
    _crear(client)

    assert _buscar(client, "cliente").status_code == 403


def test_buscar_por_documento_exige_token_y_ambos_datos(client):
    from fastapi.testclient import TestClient

    anonimo = TestClient(client.app)
    assert (
        anonimo.get("/v1/usuarios/documento", params={"tipo_documento": "CC", "numero_documento": "1"}).status_code
        == 401
    )
    assert client.get("/v1/usuarios/documento", params={"tipo_documento": "CC"}).status_code == 422


def test_un_socio_no_puede_leer_la_cuenta_completa(client):
    from tests.conftest import token_de

    creado = _crear(client).json()
    socio = {"Authorization": f"Bearer {token_de(str(uuid4()), 'socio')}"}

    assert client.get(f"/v1/usuarios/{creado['usuario_id']}", headers=socio).status_code == 403
    assert (
        client.patch(f"/v1/usuarios/{creado['usuario_id']}/perfil", json={"nombre": "X", "apellidos": "Y"}, headers=socio).status_code
        == 404
    )
