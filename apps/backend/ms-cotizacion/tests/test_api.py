from uuid import UUID

from .conftest import DATOS_VALIDOS

RUTA = "/v1/cotizaciones"


def _solicitar(client, producto="PROTECCION_DISPOSITIVO", **datos):
    return client.post(RUTA, json={"producto": producto, "datosRiesgo": {**DATOS_VALIDOS, **datos}})


# Escenario: Solicitud válida
def test_solicitud_valida_devuelve_cotizacion_id_y_oferta(client):
    respuesta = _solicitar(client)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    UUID(cuerpo["cotizacionId"])
    assert cuerpo["producto"] == "PROTECCION_DISPOSITIVO"
    assert cuerpo["estado"] == "oferta_vigente"
    assert cuerpo["moneda"] == "COP"
    assert cuerpo["prima"] == "115000.00"
    assert cuerpo["venceEn"].startswith("2026-10-07T12:00:00")
    assert [c["codigo"] for c in cuerpo["coberturas"]] == ["ROBO", "PANTALLA", "HURTO_CALIFICADO"]


def test_cada_solicitud_obtiene_un_cotizacion_id_distinto(client):
    ids = {_solicitar(client).json()["cotizacionId"] for _ in range(5)}

    assert len(ids) == 5


# Escenario: Dato del riesgo fuera de rango
def test_dato_fuera_de_rango_nombra_campo_y_rango_sin_cotizacion_id(client):
    respuesta = _solicitar(client, valorDispositivo=50_000)

    assert respuesta.status_code == 422
    assert respuesta.json() == {
        "codigo": "dato_riesgo_fuera_de_rango",
        "mensaje": "'valorDispositivo' fuera de rango: debe estar entre 300000 y 8000000",
        "campo": "valorDispositivo",
        "rangoValido": {"tipo": "entero", "min": 300_000, "max": 8_000_000},
    }


def test_producto_inexistente_es_error_de_negocio(client):
    respuesta = _solicitar(client, producto="SOAT_MOTO")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "producto_inexistente"
    assert respuesta.json()["campo"] == "producto"
    assert "cotizacionId" not in respuesta.json()


def test_cuerpo_mal_formado_usa_el_mismo_formato_de_error(client):
    respuesta = client.post(RUTA, json={"producto": "PROTECCION_DISPOSITIVO"})

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "solicitud_invalida"
    assert respuesta.json()["campo"] == "datosRiesgo"


def test_health_metrics_y_correlacion(client):
    salud = client.get("/health", headers={"X-Correlation-Id": "c-123"})

    assert salud.json() == {"status": "ok"}
    assert salud.headers["X-Correlation-Id"] == "c-123"
    assert "http_request_duration_seconds" in client.get("/metrics").text


def test_app_real_compone_los_stubs():
    from fastapi.testclient import TestClient

    from app.main import crear_app

    respuesta = TestClient(crear_app()).post(
        RUTA, json={"producto": "PROTECCION_DISPOSITIVO", "datosRiesgo": DATOS_VALIDOS}
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["prima"] == "89000.00"
