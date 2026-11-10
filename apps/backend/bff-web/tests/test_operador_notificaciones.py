import json

import httpx

from tests.conftest import token

USUARIOS = [f"10000000-0000-4000-8000-{indice:012d}" for indice in range(51)]


def _auth(client, rol="operador"):
    return {"Authorization": f"Bearer {token(client, rol)}", "X-Correlation-Id": "corr-entrada"}


def _usuario(usuario_id: str, nombre: str = "Ana", apellidos: str = "Ruiz") -> dict:
    return {
        "usuario_id": usuario_id,
        "nombre": nombre,
        "apellidos": apellidos,
        "email": "ana@correo.com",
        "numero_documento": "1020",
        "estado": "ACTIVO",
        "rol": "cliente",
    }


def _cabeceras_reenviadas(peticion: httpx.Request) -> None:
    assert peticion.headers["Authorization"].startswith("Bearer ")
    assert peticion.headers["X-Correlation-Id"] == "corr-test"


def test_audiencia_une_nombres_en_tandas_de_50(client, nucleo_notificaciones, nucleo_identidad):
    nucleo_notificaciones.respuestas[("GET", "/v1/notificaciones/audiencia")] = lambda _: httpx.Response(
        200,
        json={"usuarios": [{"usuarioId": usuario_id, "dispositivosActivos": 1} for usuario_id in USUARIOS]},
    )

    def listar(request: httpx.Request) -> httpx.Response:
        ids = request.url.params.get_list("ids")
        assert len(ids) <= 50
        assert request.url.params["rol"] == "cliente"
        return httpx.Response(
            200,
            json={
                "usuarios": [_usuario(usuario_id, nombre=f"N{usuario_id[-2:]}") for usuario_id in ids],
                "pagina": 1,
                "hay_mas": False,
            },
        )

    nucleo_identidad.respuestas[("GET", "/v1/usuarios")] = listar

    respuesta = client.get("/v1/operador/notificaciones/audiencia", headers=_auth(client))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()["usuarios"]
    assert [fila["usuarioId"] for fila in cuerpo] == USUARIOS
    assert cuerpo[0]["nombre"] == "N00"
    assert cuerpo[0]["apellidos"] == "Ruiz"
    assert cuerpo[0]["dispositivosActivos"] == 1

    consultas = [p for p in nucleo_identidad.peticiones if p.url.path == "/v1/usuarios"]
    assert len(consultas) == 2
    assert len(consultas[0].url.params.get_list("ids")) == 50
    assert len(consultas[1].url.params.get_list("ids")) == 1
    _cabeceras_reenviadas(nucleo_notificaciones.peticiones[-1])
    _cabeceras_reenviadas(consultas[0])


def test_poliza_desconocida_no_llama_a_notificaciones(client, nucleo_polizas, nucleo_notificaciones):
    antes = len(nucleo_notificaciones.peticiones)
    respuesta = client.post(
        "/v1/operador/notificaciones/difusiones",
        headers=_auth(client),
        json={
            "titulo": "Aviso",
            "cuerpo": "Texto",
            "audiencia": {"tipo": "todos"},
            "poliza": "POL-NO-EXISTE",
        },
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "poliza_desconocida"
    assert len(nucleo_notificaciones.peticiones) == antes
    assert nucleo_polizas.peticiones[-1].url.path == "/v1/polizas/numero/POL-NO-EXISTE"
    _cabeceras_reenviadas(nucleo_polizas.peticiones[-1])


def test_difusion_con_poliza_conocida_reenvia_el_cuerpo(client, nucleo_polizas, nucleo_notificaciones):
    nucleo_polizas.respuestas[("GET", "/v1/polizas/numero/POL-1")] = lambda _: httpx.Response(
        200, json={"numero": "POL-1"}
    )
    nucleo_notificaciones.respuestas[("POST", "/v1/notificaciones/difusiones")] = lambda _: httpx.Response(
        201, json={"difusionId": "c2d4", "enviadas": 1, "fallidas": 0, "sinDispositivo": 1}
    )

    respuesta = client.post(
        "/v1/operador/notificaciones/difusiones",
        headers=_auth(client),
        json={
            "titulo": "Aviso",
            "cuerpo": "Texto",
            "audiencia": {"tipo": "usuarios", "usuarioIds": [USUARIOS[0], USUARIOS[1]]},
            "poliza": "POL-1",
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["enviadas"] == 1
    enviado = json.loads(nucleo_notificaciones.peticiones[-1].content)
    assert enviado == {
        "titulo": "Aviso",
        "cuerpo": "Texto",
        "audiencia": {"tipo": "usuarios", "usuarioIds": [USUARIOS[0], USUARIOS[1]]},
        "poliza": "POL-1",
    }
    _cabeceras_reenviadas(nucleo_notificaciones.peticiones[-1])


def test_historial_reenvia_limite_y_antes_de(client, nucleo_notificaciones):
    nucleo_notificaciones.respuestas[("GET", "/v1/notificaciones/difusiones")] = lambda _: httpx.Response(
        200, json={"items": []}
    )

    respuesta = client.get(
        "/v1/operador/notificaciones/difusiones",
        headers=_auth(client),
        params={"limite": 10, "antesDe": "2026-11-09T13:05:00Z"},
    )

    assert respuesta.status_code == 200
    params = nucleo_notificaciones.peticiones[-1].url.params
    assert params["limite"] == "10"
    assert params["antesDe"] == "2026-11-09T13:05:00Z"
    _cabeceras_reenviadas(nucleo_notificaciones.peticiones[-1])


def test_asesor_recibe_403_en_las_tres_rutas_sin_llamar_al_nucleo(
    client, nucleo_notificaciones, nucleo_identidad, nucleo_polizas
):
    headers = _auth(client, "asesor")
    antes = (
        len(nucleo_notificaciones.peticiones),
        len(nucleo_identidad.peticiones),
        len(nucleo_polizas.peticiones),
    )

    assert client.get("/v1/operador/notificaciones/audiencia", headers=headers).status_code == 403
    assert (
        client.post(
            "/v1/operador/notificaciones/difusiones",
            headers=headers,
            json={"titulo": "Aviso", "cuerpo": "Texto", "audiencia": {"tipo": "todos"}},
        ).status_code
        == 403
    )
    assert client.get("/v1/operador/notificaciones/difusiones", headers=headers).status_code == 403
    assert (
        len(nucleo_notificaciones.peticiones),
        len(nucleo_identidad.peticiones),
        len(nucleo_polizas.peticiones),
    ) == antes
