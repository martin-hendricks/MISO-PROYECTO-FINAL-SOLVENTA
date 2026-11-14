from uuid import uuid4

import pytest

from tests.conftest import token_de

BODY_ALTA = {
    "tipo_documento": "CC",
    "numero_documento": "1012345678",
    "email": "camila@correo.com",
    "password": "clave-secreta-123",
}


def _crear(client, **overrides):
    return client.post("/v1/usuarios", json={**BODY_ALTA, **overrides})


def _headers(rol: str, uid: str | None = None):
    return {"Authorization": f"Bearer {token_de(uid or str(uuid4()), rol)}"}


# --- GET /v1/clientes ---------------------------------------------------------


def test_listar_clientes_devuelve_solo_usuarios_con_rol_cliente(client):
    cliente = _crear(client, nombre="Camila", apellidos="Restrepo").json()
    _crear(client, email="asesor@solventa.com", numero_documento="999")

    respuesta = client.get("/v1/clientes", headers=_headers("operador"))

    assert respuesta.status_code == 200
    ids = {item["clienteId"] for item in respuesta.json()["clientes"]}
    assert cliente["usuario_id"] in ids


def test_listar_clientes_shape_incluye_los_campos_del_backoffice(client):
    _crear(client, nombre="Camila", apellidos="Restrepo")

    respuesta = client.get("/v1/clientes", headers=_headers("asesor"))

    item = respuesta.json()["clientes"][0]
    assert set(item.keys()) == {"clienteId", "nombre", "apellidos", "documento", "canal", "estado", "consentimiento"}
    assert item["documento"] == {"tipo": "CC", "numero": "1012345678"}
    assert item["estado"] == "activo"
    assert item["nombre"] == "Camila"
    assert item["apellidos"] == "Restrepo"


def test_listar_clientes_consentimiento_resuelto_segun_los_servicios_externos(client, consentimiento, perfilamiento):
    _crear(client)
    consentimiento.vigente_valor = True
    perfilamiento.pendiente_valor = False

    respuesta = client.get("/v1/clientes", headers=_headers("operador"))

    assert respuesta.json()["clientes"][0]["consentimiento"] == "habeas_data"


def test_listar_clientes_originacion_abierta_prevalece_sobre_habeas_data(client, consentimiento, perfilamiento):
    _crear(client)
    consentimiento.vigente_valor = True
    perfilamiento.pendiente_valor = True

    respuesta = client.get("/v1/clientes", headers=_headers("operador"))

    assert respuesta.json()["clientes"][0]["consentimiento"] == "hipotecario_pendiente"


def test_listar_clientes_sin_consentimiento_ni_originacion_es_revocado(client, consentimiento, perfilamiento):
    _crear(client)
    consentimiento.vigente_valor = False
    perfilamiento.pendiente_valor = False

    respuesta = client.get("/v1/clientes", headers=_headers("operador"))

    assert respuesta.json()["clientes"][0]["consentimiento"] == "revocado"


@pytest.mark.parametrize("rol", ["cliente", "socio"])
def test_listar_clientes_prohibido_para_roles_no_backoffice(client, rol):
    respuesta = client.get("/v1/clientes", headers=_headers(rol))

    assert respuesta.status_code == 403


def test_listar_clientes_exige_token(client):
    from fastapi.testclient import TestClient

    anonimo = TestClient(client.app)
    assert anonimo.get("/v1/clientes").status_code == 401


# --- GET /v1/clientes/{usuario_id} -------------------------------------------


def test_consultar_cliente_devuelve_la_ficha(client):
    creado = _crear(client, nombre="Camila", apellidos="Restrepo").json()

    respuesta = client.get(f"/v1/clientes/{creado['usuario_id']}", headers=_headers("asesor"))

    assert respuesta.status_code == 200
    assert respuesta.json()["clienteId"] == creado["usuario_id"]


def test_consultar_cliente_inexistente_es_404(client):
    respuesta = client.get(f"/v1/clientes/{uuid4()}", headers=_headers("operador"))

    assert respuesta.status_code == 404


def test_consultar_cliente_prohibido_para_cliente(client):
    creado = _crear(client).json()

    respuesta = client.get(f"/v1/clientes/{creado['usuario_id']}", headers=_headers("cliente"))

    assert respuesta.status_code == 403


# --- PATCH /v1/clientes/{usuario_id}/estado ----------------------------------


def test_actualizar_estado_desactiva_el_cliente(client):
    creado = _crear(client).json()

    respuesta = client.patch(
        f"/v1/clientes/{creado['usuario_id']}/estado",
        json={"estado": "inactivo"},
        headers=_headers("operador"),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "inactivo"

    ficha = client.get(f"/v1/clientes/{creado['usuario_id']}", headers=_headers("operador"))
    assert ficha.json()["estado"] == "inactivo"


def test_actualizar_estado_reactiva_el_cliente(client):
    creado = _crear(client).json()
    client.patch(
        f"/v1/clientes/{creado['usuario_id']}/estado", json={"estado": "inactivo"}, headers=_headers("operador")
    )

    respuesta = client.patch(
        f"/v1/clientes/{creado['usuario_id']}/estado",
        json={"estado": "activo"},
        headers=_headers("asesor"),
    )

    assert respuesta.json()["estado"] == "activo"


def test_actualizar_estado_con_valor_invalido_es_422(client):
    creado = _crear(client).json()

    respuesta = client.patch(
        f"/v1/clientes/{creado['usuario_id']}/estado",
        json={"estado": "bloqueado"},
        headers=_headers("operador"),
    )

    assert respuesta.status_code == 422


def test_actualizar_estado_inexistente_es_404(client):
    respuesta = client.patch(
        f"/v1/clientes/{uuid4()}/estado", json={"estado": "inactivo"}, headers=_headers("operador")
    )

    assert respuesta.status_code == 404


def test_actualizar_estado_prohibido_para_cliente(client):
    creado = _crear(client).json()

    respuesta = client.patch(
        f"/v1/clientes/{creado['usuario_id']}/estado",
        json={"estado": "inactivo"},
        headers=_headers("cliente"),
    )

    assert respuesta.status_code == 403


# --- PATCH /v1/clientes/{usuario_id}/rol -------------------------------------


def test_actualizar_rol_operador_puede_promover_un_cliente_a_asesor(client):
    creado = _crear(client).json()

    respuesta = client.patch(
        f"/v1/clientes/{creado['usuario_id']}/rol",
        json={"rol": "asesor"},
        headers=_headers("operador"),
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "asesor"


def test_actualizar_rol_prohibido_para_asesor(client):
    creado = _crear(client).json()

    respuesta = client.patch(
        f"/v1/clientes/{creado['usuario_id']}/rol",
        json={"rol": "asesor"},
        headers=_headers("asesor"),
    )

    assert respuesta.status_code == 403


def test_actualizar_rol_prohibido_para_cliente(client):
    creado = _crear(client).json()

    respuesta = client.patch(
        f"/v1/clientes/{creado['usuario_id']}/rol",
        json={"rol": "asesor"},
        headers=_headers("cliente"),
    )

    assert respuesta.status_code == 403


def test_actualizar_rol_con_valor_invalido_es_422(client):
    creado = _crear(client).json()

    respuesta = client.patch(
        f"/v1/clientes/{creado['usuario_id']}/rol",
        json={"rol": "socio"},
        headers=_headers("operador"),
    )

    assert respuesta.status_code == 422


def test_actualizar_rol_inexistente_es_404(client):
    respuesta = client.patch(
        f"/v1/clientes/{uuid4()}/rol", json={"rol": "asesor"}, headers=_headers("operador")
    )

    assert respuesta.status_code == 404
