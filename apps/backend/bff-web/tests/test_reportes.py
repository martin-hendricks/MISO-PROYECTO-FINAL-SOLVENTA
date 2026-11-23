import httpx

from tests.conftest import token

REPORTE_REGULADOR = {
    "formato": "interno",
    "generadoEn": "2026-11-06T00:00:00Z",
    "contenido": [{"numero": "POL-77001-CO", "estado": "VIGENTE"}],
}

REPORTE_REASEGURADORA = {
    "formato": "interno",
    "generadoEn": "2026-11-06T00:00:00Z",
    "contenido": [{"numero": "POL-77001-CO", "siniestralidad": "0"}],
}


def _auth(client):
    return {"Authorization": f"Bearer {token(client, 'operador')}"}


def test_reporte_regulador_devuelve_lo_que_responde_el_nucleo(client, nucleo_polizas):
    nucleo_polizas.respuestas[("GET", "/v1/reportes/regulador")] = lambda _: httpx.Response(
        200, json=REPORTE_REGULADOR
    )

    respuesta = client.get("/v1/operador/reportes/regulador", headers=_auth(client))

    assert respuesta.status_code == 200
    assert respuesta.json() == REPORTE_REGULADOR


def test_reporte_reaseguradora_devuelve_lo_que_responde_el_nucleo(client, nucleo_polizas):
    nucleo_polizas.respuestas[("GET", "/v1/reportes/reaseguradora")] = lambda _: httpx.Response(
        200, json=REPORTE_REASEGURADORA
    )

    respuesta = client.get("/v1/operador/reportes/reaseguradora", headers=_auth(client))

    assert respuesta.status_code == 200
    assert respuesta.json() == REPORTE_REASEGURADORA


def test_reporte_regulador_sin_fechas_usa_rango_por_defecto(client, nucleo_polizas):
    nucleo_polizas.respuestas[("GET", "/v1/reportes/regulador")] = lambda _: httpx.Response(
        200, json=REPORTE_REGULADOR
    )

    client.get("/v1/operador/reportes/regulador", headers=_auth(client))

    peticion = nucleo_polizas.peticiones[-1]
    assert "desde" in peticion.url.params
    assert "hasta" in peticion.url.params


def test_reporte_regulador_respeta_fechas_explicitas(client, nucleo_polizas):
    nucleo_polizas.respuestas[("GET", "/v1/reportes/regulador")] = lambda _: httpx.Response(
        200, json=REPORTE_REGULADOR
    )

    client.get(
        "/v1/operador/reportes/regulador?desde=2026-01-01&hasta=2026-01-31",
        headers=_auth(client),
    )

    peticion = nucleo_polizas.peticiones[-1]
    assert peticion.url.params["desde"] == "2026-01-01"
    assert peticion.url.params["hasta"] == "2026-01-31"


def test_reporte_regulador_requiere_rol_operador(client):
    token_cliente = token(client, "cliente")
    respuesta = client.get(
        "/v1/operador/reportes/regulador", headers={"Authorization": f"Bearer {token_cliente}"}
    )
    assert respuesta.status_code == 403


def test_reporte_reaseguradora_requiere_rol_operador(client):
    token_asesor = token(client, "asesor")
    respuesta = client.get(
        "/v1/operador/reportes/reaseguradora", headers={"Authorization": f"Bearer {token_asesor}"}
    )
    assert respuesta.status_code == 403


def test_reportes_sin_token_responde_401(client):
    assert client.get("/v1/operador/reportes/regulador").status_code == 401
    assert client.get("/v1/operador/reportes/reaseguradora").status_code == 401
