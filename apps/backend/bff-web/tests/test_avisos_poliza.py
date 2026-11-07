import httpx

from tests.conftest import token

POLIZA_POR_VENCER = {
    "numero": "POL-77001-CO",
    "producto": "soat-motocicleta",
    "fin_vigencia": "2026-11-20",
    "renovable": True,
}


def _auth(client):
    return {"Authorization": f"Bearer {token(client, 'cliente')}"}


def test_polizas_por_vencer_devuelve_lista_traducida(client, nucleo_polizas):
    nucleo_polizas.respuestas[("GET", "/v1/polizas/por-vencer")] = lambda _: httpx.Response(
        200, json=[POLIZA_POR_VENCER]
    )

    respuesta = client.get("/v1/cliente/polizas/por-vencer", headers=_auth(client))

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["polizas"] == [
        {
            "numero": "POL-77001-CO",
            "ramo": "SOAT motocicleta",
            "descripcion": "Cubre la atención de víctimas de un accidente de tránsito en motocicleta.",
            "venceEn": "2026-11-20",
            "renovable": True,
        }
    ]


def test_polizas_por_vencer_sin_resultados_devuelve_lista_vacia(client, nucleo_polizas):
    nucleo_polizas.respuestas[("GET", "/v1/polizas/por-vencer")] = lambda _: httpx.Response(200, json=[])

    respuesta = client.get("/v1/cliente/polizas/por-vencer", headers=_auth(client))

    assert respuesta.status_code == 200
    assert respuesta.json() == {"polizas": []}


def test_polizas_por_vencer_envia_usuario_id_y_ventana_por_defecto(client, nucleo_polizas):
    nucleo_polizas.respuestas[("GET", "/v1/polizas/por-vencer")] = lambda _: httpx.Response(200, json=[])

    client.get("/v1/cliente/polizas/por-vencer", headers=_auth(client))

    peticion = nucleo_polizas.peticiones[-1]
    assert peticion.url.params["dias"] == "30"
    assert "usuario_id" in peticion.url.params


def test_polizas_por_vencer_sin_renovable_cae_a_false(client, nucleo_polizas):
    sin_renovable = {k: v for k, v in POLIZA_POR_VENCER.items() if k != "renovable"}
    nucleo_polizas.respuestas[("GET", "/v1/polizas/por-vencer")] = lambda _: httpx.Response(
        200, json=[sin_renovable]
    )

    respuesta = client.get("/v1/cliente/polizas/por-vencer", headers=_auth(client))

    assert respuesta.json()["polizas"][0]["renovable"] is False


def test_polizas_por_vencer_requiere_rol_cliente(client):
    token_operador = token(client, "operador")
    respuesta = client.get(
        "/v1/cliente/polizas/por-vencer", headers={"Authorization": f"Bearer {token_operador}"}
    )
    assert respuesta.status_code == 403


def test_polizas_por_vencer_sin_token_responde_401(client):
    respuesta = client.get("/v1/cliente/polizas/por-vencer")
    assert respuesta.status_code == 401
