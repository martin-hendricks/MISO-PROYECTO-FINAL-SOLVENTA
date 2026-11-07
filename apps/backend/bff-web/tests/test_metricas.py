import httpx

from tests.conftest import token

METRICAS = {
    "conteos": [
        {"tipo": "PolizaEmitida", "fecha": "2026-11-01", "cantidad": 3},
        {"tipo": "PolizaCancelada", "fecha": "2026-11-02", "cantidad": 1},
    ]
}


def _auth(client):
    return {"Authorization": f"Bearer {token(client, 'operador')}"}


def test_metricas_devuelve_lo_que_responde_el_nucleo(client, nucleo_analitica):
    nucleo_analitica.respuestas[("GET", "/v1/metricas")] = lambda _: httpx.Response(200, json=METRICAS)

    respuesta = client.get("/v1/operador/metricas", headers=_auth(client))

    assert respuesta.status_code == 200
    assert respuesta.json() == METRICAS


def test_metricas_sin_fechas_usa_rango_por_defecto(client, nucleo_analitica):
    nucleo_analitica.respuestas[("GET", "/v1/metricas")] = lambda _: httpx.Response(200, json=METRICAS)

    client.get("/v1/operador/metricas", headers=_auth(client))

    peticion = nucleo_analitica.peticiones[-1]
    assert "desde" in peticion.url.params
    assert "hasta" in peticion.url.params


def test_metricas_respeta_fechas_explicitas(client, nucleo_analitica):
    nucleo_analitica.respuestas[("GET", "/v1/metricas")] = lambda _: httpx.Response(200, json=METRICAS)

    client.get(
        "/v1/operador/metricas?desde=2026-01-01&hasta=2026-01-31",
        headers=_auth(client),
    )

    peticion = nucleo_analitica.peticiones[-1]
    assert peticion.url.params["desde"] == "2026-01-01"
    assert peticion.url.params["hasta"] == "2026-01-31"


def test_metricas_requiere_rol_operador(client):
    token_cliente = token(client, "cliente")
    respuesta = client.get("/v1/operador/metricas", headers={"Authorization": f"Bearer {token_cliente}"})
    assert respuesta.status_code == 403


def test_metricas_sin_token_responde_401(client):
    assert client.get("/v1/operador/metricas").status_code == 401
