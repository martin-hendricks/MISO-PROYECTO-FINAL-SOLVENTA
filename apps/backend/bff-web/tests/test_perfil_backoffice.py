import httpx

from tests.conftest import token

UID = "11111111-1111-1111-1111-111111111111"


def _auth(client, rol):
    return {"Authorization": f"Bearer {token(client, rol)}"}


def test_asesor_lee_su_perfil(client, nucleo_identidad):
    nucleo_identidad.respuestas[("GET", f"/v1/usuarios/{UID}")] = lambda _: httpx.Response(
        200,
        json={
            "usuario_id": UID,
            "email": "persona@solventa.com",
            "nombre": "Camila",
            "apellidos": "Restrepo",
            "rol": "asesor",
        },
    )

    respuesta = client.get("/v1/backoffice/perfil", headers=_auth(client, "asesor"))

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "usuarioId": UID,
        "correo": "persona@solventa.com",
        "nombre": "Camila",
        "apellidos": "Restrepo",
        "rol": "asesor",
    }


def test_operador_lee_su_perfil(client, nucleo_identidad):
    nucleo_identidad.respuestas[("GET", f"/v1/usuarios/{UID}")] = lambda _: httpx.Response(
        200,
        json={
            "usuario_id": UID,
            "email": "operador@solventa.com",
            "nombre": "Jorge",
            "apellidos": "Nieto",
            "rol": "operador",
        },
    )

    respuesta = client.get("/v1/backoffice/perfil", headers=_auth(client, "operador"))

    assert respuesta.status_code == 200
    assert respuesta.json()["rol"] == "operador"


def test_cliente_no_puede_leer_el_perfil_de_backoffice(client):
    respuesta = client.get("/v1/backoffice/perfil", headers=_auth(client, "cliente"))

    assert respuesta.status_code == 403


def test_perfil_sin_nombre_ni_apellidos_devuelve_vacio(client, nucleo_identidad):
    nucleo_identidad.respuestas[("GET", f"/v1/usuarios/{UID}")] = lambda _: httpx.Response(
        200,
        json={"usuario_id": UID, "email": "persona@solventa.com", "rol": "asesor"},
    )

    respuesta = client.get("/v1/backoffice/perfil", headers=_auth(client, "asesor"))

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == ""
    assert respuesta.json()["apellidos"] == ""
