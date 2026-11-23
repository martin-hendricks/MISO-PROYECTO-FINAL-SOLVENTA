"""Pacto bff-movil -> ms-cotizacion (HU-88, PI-01): cotización, aceptación y billetera del canal móvil.

Cada interacción exige solo los campos que bff-movil lee del núcleo, y cada test pasa la
respuesta del mock por la misma traducción que usa la ruta. Así el pacto no se queda
corto (el test fallaría con un 502) ni pide de más (el núcleo puede evolucionar el resto).
"""

from decimal import Decimal
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.clients.nucleo import ClienteNucleo
from app.routers.cliente import _cotizacion_de_poliza, _exigir, _oferta_movil

pact_v3 = pytest.importorskip("pact.v3")
match = pact_v3.match

pytestmark = pytest.mark.contract

PACTOS = Path(__file__).resolve().parents[2] / "pacts"
DECIMAL = r"^-?\d+(\.\d+)?$"
MONEDA = r"^[A-Z]{3}$"
# Pact exige que la regex cubra el valor completo: ISO 8601 con fracción y zona opcionales.
FECHA_ISO = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"

# Ids fijos que el proveedor siembra en sus estados. Las Idempotency-Key van literales:
# distinguen las interacciones que comparten método y ruta (éxito y rechazo) en el mock.
COTIZACION_ID = "6f1c2b9e-8d4a-4f7b-9c3e-1a2b3c4d5e6f"
OFERTA_ID = "9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d"
OFERTA_INEXISTENTE = "00000000-0000-4000-8000-000000000000"

USUARIO_ID = "0b6f3c1e-2d4a-5b7c-8d9e-0f1a2b3c4d5e"
SOCIO_ID = "1c7a4d2f-3e5b-5c8d-9e0f-1a2b3c4d5e6f"
CONSENTIMIENTO_ID = "2d8b5e3a-4f6c-5d9e-8f1a-2b3c4d5e6f7a"
PERFIL_ID = "3e9c6f4b-5a7d-5e0f-9a2b-3c4d5e6f7a8b"

DATOS_RIESGO = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}
DATOS_RIESGO_FUERA_DE_RANGO = {"cilindraje_cc": 5000, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}

SOLICITUD = {
    "usuario_id": match.uuid(USUARIO_ID),
    "socio_id": match.uuid(SOCIO_ID),
    "consentimiento_id": match.uuid(CONSENTIMIENTO_ID),
    "producto": match.str("soat-motocicleta"),
    "canal": "movil",
    "datos_riesgo": match.like(DATOS_RIESGO),
}

COTIZACION = {
    "cotizacion_id": match.uuid(COTIZACION_ID),
    "estado": match.str("cotizada"),
    "prima": match.regex("140500.00", regex=DECIMAL),
    "moneda": match.regex("COP", regex=MONEDA),
    "vence_en": match.regex("2026-10-30T13:00:00Z", regex=FECHA_ISO),
}

ACEPTACION = {"perfil_id": match.uuid(PERFIL_ID), "score": match.regex("0.5000", regex=DECIMAL)}


@pytest.fixture(scope="module")
def nucleo():
    pacto = pact_v3.Pact("bff-movil", "ms-cotizacion").with_specification("V4")
    (
        pacto.upon_receiving("una solicitud de cotización desde el canal móvil")
        .with_request("POST", "/v1/cotizaciones")
        .with_header("Idempotency-Key", "clave-cotizacion-0001")
        .with_body(SOLICITUD, content_type="application/json")
        .will_respond_with(201)
        .with_body(COTIZACION)
    )
    (
        pacto.upon_receiving("una solicitud de cotización móvil con un dato de riesgo fuera de rango")
        .with_request("POST", "/v1/cotizaciones")
        .with_header("Idempotency-Key", "clave-cotizacion-0002")
        .with_body({**SOLICITUD, "datos_riesgo": DATOS_RIESGO_FUERA_DE_RANGO}, content_type="application/json")
        .will_respond_with(422)
        .with_body({"mensaje": match.str("Fuera de rango")})
    )
    (
        pacto.upon_receiving("la reconsulta de una cotización vigente desde el canal móvil")
        .given("existe una cotización vigente", parameters={"cotizacion_id": COTIZACION_ID})
        .with_request("GET", f"/v1/cotizaciones/{COTIZACION_ID}")
        .will_respond_with(200)
        .with_body({**COTIZACION, "producto": match.str("soat-motocicleta")})
    )
    (
        pacto.upon_receiving("la aceptación móvil de una oferta que la suscripción acepta")
        .given("existe una cotización vigente que la suscripción acepta", parameters={"cotizacion_id": COTIZACION_ID})
        .with_request("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")
        .with_header("Idempotency-Key", "clave-aceptacion-0001")
        .with_body(ACEPTACION, content_type="application/json")
        .will_respond_with(201)
        .with_body(
            {
                "decision": "ACEPTADA",
                "cotizacion_id": match.uuid(COTIZACION_ID),
                "oferta_id": match.uuid(OFERTA_ID),
                "prima": match.regex("140500.00", regex=DECIMAL),
            }
        )
    )
    (
        pacto.upon_receiving("la aceptación móvil de una oferta que la suscripción rechaza")
        .given("existe una cotización vigente que la suscripción rechaza", parameters={"cotizacion_id": COTIZACION_ID})
        .with_request("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")
        .with_header("Idempotency-Key", "clave-aceptacion-0002")
        .with_body(ACEPTACION, content_type="application/json")
        .will_respond_with(201)
        .with_body({"decision": "RECHAZADA", "motivo": match.str("regla de suscripción")})
    )
    (
        pacto.upon_receiving("la consulta móvil de la cotización de una oferta emitida")
        .given("existe una oferta emitida", parameters={"oferta_id": OFERTA_ID})
        .with_request("GET", f"/v1/cotizaciones/por-oferta/{OFERTA_ID}")
        .will_respond_with(200)
        .with_body({"producto": match.str("soat-motocicleta")})
    )
    (
        pacto.upon_receiving("la consulta móvil de la cotización de una oferta que no existe")
        .with_request("GET", f"/v1/cotizaciones/por-oferta/{OFERTA_INEXISTENTE}")
        .will_respond_with(404)
    )
    with pacto.serve() as servidor:
        yield ClienteNucleo({"ms-cotizacion": str(servidor.url)})
    PACTOS.mkdir(parents=True, exist_ok=True)
    pacto.write_file(PACTOS, overwrite=True)


def _cotizar(nucleo: ClienteNucleo, clave: str, datos_riesgo: dict) -> dict:
    return nucleo.cotizar(
        idempotency_key=clave,
        usuario_id=USUARIO_ID,
        socio_id=SOCIO_ID,
        consentimiento_id=CONSENTIMIENTO_ID,
        producto="soat-motocicleta",
        canal="movil",
        datos_riesgo=datos_riesgo,
    )


def _aceptar(nucleo: ClienteNucleo, clave: str) -> dict:
    return nucleo.aceptar_oferta(
        cotizacion_id=COTIZACION_ID, idempotency_key=clave, perfil_id=PERFIL_ID, score="0.5000"
    )


def test_cotizacion(nucleo):
    vista = _oferta_movil(_cotizar(nucleo, "clave-cotizacion-0001", DATOS_RIESGO), "SOAT motocicleta")

    assert (vista["cotizacionId"], vista["moneda"]) == (COTIZACION_ID, "COP")


def test_cotizacion_con_dato_fuera_de_rango_llega_como_422_con_el_mensaje(nucleo):
    with pytest.raises(HTTPException) as rechazo:
        _cotizar(nucleo, "clave-cotizacion-0002", DATOS_RIESGO_FUERA_DE_RANGO)

    assert (rechazo.value.status_code, rechazo.value.detail) == (422, "Fuera de rango")


def test_reconsulta_de_una_cotizacion(nucleo):
    datos = _exigir(nucleo.reconsultar(COTIZACION_ID), "producto")

    vista = _oferta_movil(datos, datos["producto"])
    assert (vista["cotizacionId"], vista["ramo"]) == (COTIZACION_ID, "soat-motocicleta")


def test_aceptacion_aceptada_entrega_lo_necesario_para_cobrar_y_emitir(nucleo):
    aceptacion = _exigir(_aceptar(nucleo, "clave-aceptacion-0001"), "decision", "oferta_id", "cotizacion_id", "prima")

    assert str(aceptacion["decision"]).upper() == "ACEPTADA"
    assert (aceptacion["oferta_id"], aceptacion["cotizacion_id"]) == (OFERTA_ID, COTIZACION_ID)
    assert Decimal(str(aceptacion["prima"])) > 0


def test_aceptacion_rechazada_entrega_el_motivo(nucleo):
    aceptacion = _exigir(_aceptar(nucleo, "clave-aceptacion-0002"), "decision", "motivo")

    assert str(aceptacion["decision"]).upper() == "RECHAZADA"
    assert aceptacion["motivo"]


def test_billetera_toma_el_ramo_de_la_cotizacion_de_la_oferta(nucleo):
    cotizacion = _cotizacion_de_poliza(nucleo, {"oferta_id": OFERTA_ID})

    assert cotizacion["producto"] == "soat-motocicleta"


def test_billetera_tolera_una_oferta_sin_cotizacion(nucleo):
    assert _cotizacion_de_poliza(nucleo, {"oferta_id": OFERTA_INEXISTENTE}) == {}
