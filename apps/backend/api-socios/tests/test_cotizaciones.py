import json

import httpx
import pytest
from fastapi.testclient import TestClient

from .conftest import CABECERA_SOLO_CATALOGO, SOCIO_ID

USUARIO_ID = "11111111-1111-1111-1111-111111111111"
CONSENTIMIENTO_ID = "22222222-2222-2222-2222-222222222222"
COTIZACION_ID = "33333333-3333-3333-3333-333333333333"
CLAVE = "clave-del-socio-01"
CUERPO = {
    "tipoDocumento": "CC",
    "numeroDocumento": "1012345678",
    "producto": "viaje",
    "datosRiesgo": {"destino": "cartagena", "duracion": 7},
}
COTIZACION_NUCLEO = {
    "cotizacion_id": COTIZACION_ID,
    "usuario_id": USUARIO_ID,
    "estado": "cotizada",
    "producto": "viaje",
    "creada_en": "2026-11-18T12:00:00Z",
    "prima": "77000.00",
    "prima_neta": "70000.00",
    "gastos_expedicion": "7000.00",
    "moneda": "COP",
    "vence_en": "2026-11-18T12:30:00Z",
    "factor_riesgo_origen": "respaldo",
    "vencida": False,
}
RUTA_CONSENTIMIENTO = ("GET", f"/v1/consentimientos/{USUARIO_ID}")


def _cliente_registrado(identidad):
    identidad.respuestas[("GET", "/v1/usuarios/documento")] = lambda _: httpx.Response(
        200, json={"usuario_id": USUARIO_ID}
    )


def _consentimiento(perfilamiento, vigente: bool | None):
    if vigente is None:
        perfilamiento.respuestas[RUTA_CONSENTIMIENTO] = lambda _: httpx.Response(404, json={"codigo": "no_encontrado"})
        return
    perfilamiento.respuestas[RUTA_CONSENTIMIENTO] = lambda _: httpx.Response(
        200, json={"id": CONSENTIMIENTO_ID, "cliente_id": USUARIO_ID, "vigente": vigente}
    )


def _nucleo_cotiza(nucleo, status: int = 201):
    nucleo.respuestas[("POST", "/v1/cotizaciones")] = lambda _: httpx.Response(status, json=COTIZACION_NUCLEO)


def _cotizar(client, cuerpo=None, clave=CLAVE):
    return client.post("/v1/cotizaciones", json=cuerpo or CUERPO, headers={"Idempotency-Key": clave})


def _peticion_al_nucleo(nucleo) -> httpx.Request:
    [peticion] = [p for p in nucleo.peticiones if p.method == "POST" and p.url.path == "/v1/cotizaciones"]
    return peticion


def test_socio_cotiza_para_un_cliente_con_consentimiento(client, nucleo, identidad, perfilamiento):
    _cliente_registrado(identidad)
    _consentimiento(perfilamiento, vigente=True)
    _nucleo_cotiza(nucleo)

    respuesta = _cotizar(client)

    assert respuesta.status_code == 201
    assert respuesta.json() == {
        "cotizacionId": COTIZACION_ID,
        "estado": "cotizada",
        "producto": "viaje",
        "prima": "77000.00",
        "primaNeta": "70000.00",
        "gastosExpedicion": "7000.00",
        "moneda": "COP",
        "venceEn": "2026-11-18T12:30:00Z",
        "vencida": False,
        "consentimientoPendiente": False,
    }
    peticion = _peticion_al_nucleo(nucleo)
    assert json.loads(peticion.content) == {
        "usuario_id": USUARIO_ID,
        "socio_id": SOCIO_ID,
        "consentimiento_id": CONSENTIMIENTO_ID,
        "producto": "viaje",
        "canal": "socio",
        "datos_riesgo": {"destino": "cartagena", "duracion": 7},
    }
    assert peticion.headers["Idempotency-Key"] == f"{SOCIO_ID}:{CLAVE}"
    assert peticion.headers["Authorization"] == "Bearer token-de-socio"


@pytest.mark.parametrize("vigente", [None, False])
def test_sin_consentimiento_vigente_cotiza_y_queda_pendiente(client, nucleo, identidad, perfilamiento, vigente):
    _cliente_registrado(identidad)
    _consentimiento(perfilamiento, vigente=vigente)
    _nucleo_cotiza(nucleo)

    respuesta = _cotizar(client)

    assert respuesta.status_code == 201
    assert respuesta.json()["consentimientoPendiente"] is True
    assert json.loads(_peticion_al_nucleo(nucleo).content)["consentimiento_id"] is None


def test_reintento_con_la_misma_clave_responde_200(client, nucleo, identidad, perfilamiento):
    _cliente_registrado(identidad)
    _consentimiento(perfilamiento, vigente=True)
    _nucleo_cotiza(nucleo, status=200)

    assert _cotizar(client).status_code == 200


def test_documento_sin_cliente_es_404_y_no_cotiza(client, nucleo, perfilamiento):
    respuesta = _cotizar(client)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "cliente_no_registrado"
    assert perfilamiento.peticiones == []
    assert [p for p in nucleo.peticiones if p.method == "POST"] == []


def test_socio_sin_alcance_de_cotizacion_es_403_y_no_llama_al_nucleo(app, nucleo, identidad, perfilamiento):
    solo_catalogo = TestClient(app, headers=CABECERA_SOLO_CATALOGO)

    respuesta = solo_catalogo.post("/v1/cotizaciones", json=CUERPO, headers={"Idempotency-Key": CLAVE})

    assert respuesta.status_code == 403
    assert identidad.peticiones == []
    assert perfilamiento.peticiones == []
    assert nucleo.peticiones == []


@pytest.mark.parametrize(
    ("cuerpo", "cabeceras"),
    [
        (CUERPO, {}),
        (CUERPO, {"Idempotency-Key": "corta"}),
        ({**CUERPO, "socioId": "otro-socio"}, {"Idempotency-Key": CLAVE}),
        ({k: v for k, v in CUERPO.items() if k != "producto"}, {"Idempotency-Key": CLAVE}),
    ],
)
def test_solicitud_invalida_es_422_sin_llamar_a_nadie(client, nucleo, identidad, perfilamiento, cuerpo, cabeceras):
    respuesta = client.post("/v1/cotizaciones", json=cuerpo, headers=cabeceras)

    assert respuesta.status_code == 422
    assert identidad.peticiones == []
    assert nucleo.peticiones == []


def test_rechazo_del_nucleo_se_propaga(client, nucleo, identidad, perfilamiento):
    _cliente_registrado(identidad)
    _consentimiento(perfilamiento, vigente=True)
    nucleo.respuestas[("POST", "/v1/cotizaciones")] = lambda _: httpx.Response(
        422, json={"codigo": "dato_riesgo_fuera_de_rango", "mensaje": "duracion fuera de rango"}
    )

    respuesta = _cotizar(client)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "dato_riesgo_fuera_de_rango"


def test_socio_reconsulta_su_cotizacion(client, nucleo):
    nucleo.respuestas[("GET", f"/v1/cotizaciones/{COTIZACION_ID}")] = lambda _: httpx.Response(
        200, json=COTIZACION_NUCLEO
    )

    respuesta = client.get(f"/v1/cotizaciones/{COTIZACION_ID}")

    assert respuesta.status_code == 200
    assert respuesta.json()["cotizacionId"] == COTIZACION_ID
    assert "consentimientoPendiente" not in respuesta.json()
    [peticion] = nucleo.peticiones
    assert peticion.headers["Authorization"] == "Bearer token-de-socio"


def test_cotizacion_ajena_o_inexistente_es_404(client):
    respuesta = client.get(f"/v1/cotizaciones/{COTIZACION_ID}")

    assert respuesta.status_code == 404


def test_socio_sin_alcance_de_lectura_es_403(app, nucleo):
    solo_catalogo = TestClient(app, headers=CABECERA_SOLO_CATALOGO)

    assert solo_catalogo.get(f"/v1/cotizaciones/{COTIZACION_ID}").status_code == 403
    assert nucleo.peticiones == []
