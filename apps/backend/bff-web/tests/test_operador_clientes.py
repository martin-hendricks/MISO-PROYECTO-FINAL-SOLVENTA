import json

import httpx

from tests.conftest import token

USUARIO = "12345678-1234-4123-8123-123456789abc"


def _auth(client, rol="operador"):
    return {"Authorization": f"Bearer {token(client, rol)}"}


def _usuario(**cambios) -> dict:
    base = {
        "usuario_id": USUARIO,
        "nombre": "Ana",
        "apellidos": "Ruiz",
        "email": "ana@correo.com",
        "tipo_documento": "CC",
        "numero_documento": "102030",
        "estado": "ACTIVO",
        "rol": "cliente",
    }
    base.update(cambios)
    return base


def _listado(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        200,
        json={"usuarios": [_usuario(), _usuario(usuario_id="aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa", nombre="Luis")], "pagina": 2, "hay_mas": True},
    )


def test_listar_une_dispositivos_de_la_pagina(client, nucleo_identidad, nucleo_notificaciones):
    nucleo_identidad.respuestas[("GET", "/v1/usuarios")] = _listado

    def audiencia(request: httpx.Request) -> httpx.Response:
        assert request.url.params.get_list("usuarioIds") == [
            USUARIO,
            "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        ]
        return httpx.Response(
            200, json={"usuarios": [{"usuarioId": USUARIO, "dispositivosActivos": 2}]}
        )

    nucleo_notificaciones.respuestas[("GET", "/v1/notificaciones/audiencia")] = audiencia

    respuesta = client.get(
        "/v1/operador/clientes",
        headers=_auth(client),
        params={"q": "an", "estado": "ACTIVO", "pagina": 2},
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["pagina"] == 2
    assert cuerpo["hayMas"] is True
    assert cuerpo["clientes"][0] == {
        "usuarioId": USUARIO,
        "nombre": "Ana",
        "apellidos": "Ruiz",
        "email": "ana@correo.com",
        "documento": "102030",
        "estado": "ACTIVO",
        "dispositivosActivos": 2,
    }
    assert cuerpo["clientes"][1]["dispositivosActivos"] == 0
    consulta = nucleo_identidad.peticiones[-1].url.params
    assert consulta["rol"] == "cliente"
    assert consulta["q"] == "an"
    assert consulta["estado"] == "ACTIVO"
    assert consulta["pagina"] == "2"


def test_listar_sigue_cuando_la_audiencia_falla(client, nucleo_identidad, nucleo_notificaciones):
    nucleo_identidad.respuestas[("GET", "/v1/usuarios")] = lambda _: httpx.Response(
        200, json={"usuarios": [_usuario()], "pagina": 1, "hay_mas": False}
    )

    def caido(request):
        raise httpx.ConnectError("conexión rechazada", request=request)

    nucleo_notificaciones.respuestas[("GET", "/v1/notificaciones/audiencia")] = caido

    respuesta = client.get("/v1/operador/clientes", headers=_auth(client))

    assert respuesta.status_code == 200
    assert respuesta.json()["clientes"][0]["dispositivosActivos"] is None


def test_crear_editar_y_estado_reenvian_a_identidad(client, nucleo_identidad):
    nucleo_identidad.respuestas[("POST", "/v1/usuarios")] = lambda request: httpx.Response(
        201, json=_usuario(**_desde_alta(request))
    )
    nucleo_identidad.respuestas[("PATCH", f"/v1/usuarios/{USUARIO}")] = lambda request: httpx.Response(
        200, json=_usuario(nombre="Ana María", email="nueva@correo.com")
    )
    nucleo_identidad.respuestas[("POST", f"/v1/usuarios/{USUARIO}/estado")] = lambda request: httpx.Response(
        200, json=_usuario(estado="INACTIVO")
    )

    alta = client.post(
        "/v1/operador/clientes",
        headers=_auth(client),
        json={
            "tipoDocumento": "CC",
            "documento": "102030",
            "email": "ana@correo.com",
            "password": "secreto",
            "nombre": "Ana",
            "apellidos": "Ruiz",
        },
    )
    assert alta.status_code == 201
    assert "password" not in alta.json()
    assert alta.json()["usuarioId"] == USUARIO
    enviado = json.loads(nucleo_identidad.peticiones[-1].content)
    assert enviado["numero_documento"] == "102030"
    assert enviado["password"] == "secreto"
    assert "hash" not in enviado

    edicion = client.patch(
        f"/v1/operador/clientes/{USUARIO}",
        headers=_auth(client),
        json={"nombre": "Ana María", "apellidos": "Ruiz", "email": "nueva@correo.com"},
    )
    assert edicion.status_code == 200
    assert edicion.json()["email"] == "nueva@correo.com"
    assert json.loads(nucleo_identidad.peticiones[-1].content)["email"] == "nueva@correo.com"

    estado = client.post(
        f"/v1/operador/clientes/{USUARIO}/estado",
        headers=_auth(client),
        json={"estado": "INACTIVO"},
    )
    assert estado.status_code == 200
    assert estado.json()["estado"] == "INACTIVO"
    assert json.loads(nucleo_identidad.peticiones[-1].content) == {"estado": "INACTIVO"}


def _desde_alta(request: httpx.Request) -> dict:
    cuerpo = json.loads(request.content)
    return {
        "nombre": cuerpo["nombre"],
        "apellidos": cuerpo["apellidos"],
        "email": cuerpo["email"],
        "numero_documento": cuerpo["numero_documento"],
        "tipo_documento": cuerpo["tipo_documento"],
    }


def test_crear_mapea_409_y_editar_mapea_404(client, nucleo_identidad):
    nucleo_identidad.respuestas[("POST", "/v1/usuarios")] = lambda _: httpx.Response(
        409, json={"codigo": "email_duplicado", "mensaje": "El correo ya existe"}
    )
    conflicto = client.post(
        "/v1/operador/clientes",
        headers=_auth(client),
        json={
            "tipoDocumento": "CC",
            "documento": "102030",
            "email": "ana@correo.com",
            "password": "secreto",
            "nombre": "Ana",
            "apellidos": "Ruiz",
        },
    )
    assert conflicto.status_code == 409
    assert conflicto.json()["codigo"] == "email_duplicado"

    nucleo_identidad.respuestas[("PATCH", f"/v1/usuarios/{USUARIO}")] = lambda _: httpx.Response(
        404, json={"codigo": "no_encontrado", "mensaje": "No existe"}
    )
    ausente = client.patch(
        f"/v1/operador/clientes/{USUARIO}",
        headers=_auth(client),
        json={"nombre": "Ana", "apellidos": "Ruiz", "email": "ana@correo.com"},
    )
    assert ausente.status_code == 404
    assert ausente.json()["codigo"] == "no_encontrado"


def test_asesor_lista_y_no_escribe(client, nucleo_identidad, nucleo_notificaciones):
    nucleo_identidad.respuestas[("GET", "/v1/usuarios")] = lambda _: httpx.Response(
        200, json={"usuarios": [_usuario()], "pagina": 1, "hay_mas": False}
    )
    nucleo_notificaciones.respuestas[("GET", "/v1/notificaciones/audiencia")] = lambda _: httpx.Response(
        200, json={"usuarios": []}
    )

    headers = _auth(client, "asesor")
    listado = client.get("/v1/operador/clientes", headers=headers)
    assert listado.status_code == 200
    assert listado.json()["clientes"][0]["usuarioId"] == USUARIO

    antes_identidad = len(nucleo_identidad.peticiones)
    antes_notificaciones = len(nucleo_notificaciones.peticiones)
    assert (
        client.post(
            "/v1/operador/clientes",
            headers=headers,
            json={
                "tipoDocumento": "CC",
                "documento": "1",
                "email": "a@b.co",
                "password": "secreto",
                "nombre": "Ana",
                "apellidos": "Ruiz",
            },
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/v1/operador/clientes/{USUARIO}",
            headers=headers,
            json={"nombre": "Ana", "apellidos": "Ruiz", "email": "a@b.co"},
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"/v1/operador/clientes/{USUARIO}/estado",
            headers=headers,
            json={"estado": "INACTIVO"},
        ).status_code
        == 403
    )
    assert len(nucleo_identidad.peticiones) == antes_identidad
    assert len(nucleo_notificaciones.peticiones) == antes_notificaciones
