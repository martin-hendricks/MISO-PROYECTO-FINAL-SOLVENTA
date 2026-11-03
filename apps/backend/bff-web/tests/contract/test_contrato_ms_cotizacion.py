"""Pacto bff-web -> ms-cotizacion (HU-88, PI-01): recorrido de catálogo, cotización y emisión.

Cada interacción exige solo los campos que bff-web lee del núcleo, y cada test pasa la
respuesta del mock por la misma traducción que usa la ruta. Así el pacto no se queda
corto (el test fallaría con KeyError) ni pide de más (el núcleo puede evolucionar el resto).
"""

import asyncio
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import httpx
import pytest

from app.clients.base import RechazoDelNucleo, RecursoNoEncontrado
from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.routers.cliente import _catalogo_salida, _cotizacion_salida

pact_v3 = pytest.importorskip("pact.v3")
match = pact_v3.match

pytestmark = pytest.mark.contract

PACTOS = Path(__file__).resolve().parents[2] / "pacts"
DECIMAL = r"^-?\d+(\.\d+)?$"
# Pact exige que la regex cubra el valor completo: ISO 8601 con fracción y zona opcionales.
FECHA_ISO = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"

# Ids fijos que el proveedor siembra en sus estados. Las Idempotency-Key van literales:
# distinguen las interacciones que comparten método y ruta (éxito y rechazo) en el mock.
COTIZACION_ID = "6f1c2b9e-8d4a-4f7b-9c3e-1a2b3c4d5e6f"
OFERTA_ID = "9a8b7c6d-5e4f-4a3b-8c2d-1e0f9a8b7c6d"

SOLICITUD = {
    "usuario_id": match.uuid("0b6f3c1e-2d4a-5b7c-8d9e-0f1a2b3c4d5e"),
    "socio_id": match.uuid("1c7a4d2f-3e5b-5c8d-9e0f-1a2b3c4d5e6f"),
    "consentimiento_id": match.uuid("2d8b5e3a-4f6c-5d9e-8f1a-2b3c4d5e6f7a"),
    "producto": "soat-motocicleta",
    "canal": "web",
    "datos_riesgo": match.like({"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}),
}
DATOS_RIESGO_FUERA_DE_RANGO = {"cilindraje_cc": 5000, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}

COTIZACION = {
    "cotizacion_id": match.uuid(COTIZACION_ID),
    "estado": match.str("cotizada"),
    "prima": match.regex("140500.00", regex=DECIMAL),
    "prima_neta": match.regex("132000.00", regex=DECIMAL),
    "gastos_expedicion": match.regex("8500", regex=DECIMAL),
    "moneda": match.regex("COP", regex=r"^[A-Z]{3}$"),
    "vence_en": match.regex("2026-10-30T13:00:00Z", regex=FECHA_ISO),
}

PRODUCTO = {
    "nombre": match.str("SOAT motocicleta"),
    "moneda": match.regex("COP", regex=r"^[A-Z]{3}$"),
    "coberturas": match.each_like(
        {
            "codigo": match.str("gastos_medicos"),
            "nombre": match.str("Gastos médicos"),
            "limite": match.regex("800", regex=DECIMAL),
            "unidad_limite": match.regex("SMLDV", regex=r"^(SMLDV|MONEDA)$"),
        }
    ),
    "datos_riesgo": match.array_containing(
        [
            {
                "nombre": match.str("cilindraje_cc"),
                "tipo": "rango",
                "minimo": match.regex("50", regex=DECIMAL),
                "maximo": match.regex("1800", regex=DECIMAL),
            },
            {"nombre": match.str("ciudad_circulacion"), "tipo": "valores", "valores": match.each_like("bogota")},
        ]
    ),
}

ACEPTACION = {"perfil_id": match.uuid("3e9c6f4b-5a7d-5e0f-9a2b-3c4d5e6f7a8b"), "score": match.regex("0.5000", regex=DECIMAL)}


@pytest.fixture(scope="module")
def nucleo_url():
    pacto = pact_v3.Pact("bff-web", "ms-cotizacion").with_specification("V4")
    (
        pacto.upon_receiving("una consulta del catálogo de soat-motocicleta")
        .with_request("GET", "/v1/productos/soat-motocicleta")
        .will_respond_with(200)
        .with_body(PRODUCTO)
    )
    (
        pacto.upon_receiving("una consulta del catálogo de un ramo sin producto")
        .with_request("GET", "/v1/productos/no-existe")
        .will_respond_with(404)
    )
    (
        pacto.upon_receiving("una solicitud de cotización de soat-motocicleta")
        .with_request("POST", "/v1/cotizaciones")
        .with_header("Idempotency-Key", "clave-cotizacion-0001")
        .with_body(SOLICITUD, content_type="application/json")
        .will_respond_with(201)
        .with_body(COTIZACION)
    )
    (
        pacto.upon_receiving("una solicitud de cotización con un dato de riesgo fuera de rango")
        .with_request("POST", "/v1/cotizaciones")
        .with_header("Idempotency-Key", "clave-cotizacion-0002")
        .with_body({**SOLICITUD, "datos_riesgo": DATOS_RIESGO_FUERA_DE_RANGO}, content_type="application/json")
        .will_respond_with(422)
        .with_body({"codigo": match.str("dato_riesgo_fuera_de_rango"), "mensaje": match.str("Fuera de rango")})
    )
    (
        pacto.upon_receiving("la reconsulta de una cotización vigente")
        .given("existe una cotización vigente", parameters={"cotizacion_id": COTIZACION_ID})
        .with_request("GET", f"/v1/cotizaciones/{COTIZACION_ID}")
        .will_respond_with(200)
        .with_body({**COTIZACION, "producto": match.str("soat-motocicleta")})
    )
    (
        pacto.upon_receiving("la aceptación de una oferta que la suscripción acepta")
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
                "moneda": match.regex("COP", regex=r"^[A-Z]{3}$"),
            }
        )
    )
    (
        pacto.upon_receiving("la aceptación de una oferta que la suscripción rechaza")
        .given("existe una cotización vigente que la suscripción rechaza", parameters={"cotizacion_id": COTIZACION_ID})
        .with_request("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")
        .with_header("Idempotency-Key", "clave-aceptacion-0002")
        .with_body(ACEPTACION, content_type="application/json")
        .will_respond_with(201)
        .with_body({"decision": "RECHAZADA", "motivo": match.str("regla de suscripción")})
    )
    (
        pacto.upon_receiving("la consulta de la cotización de una oferta emitida")
        .given("existe una oferta emitida", parameters={"oferta_id": OFERTA_ID})
        .with_request("GET", f"/v1/cotizaciones/por-oferta/{OFERTA_ID}")
        .will_respond_with(200)
        .with_body(
            {
                "producto": match.str("soat-motocicleta"),
                "prima": match.regex("140500.00", regex=DECIMAL),
                "moneda": match.regex("COP", regex=r"^[A-Z]{3}$"),
            }
        )
    )
    with pacto.serve() as servidor:
        yield str(servidor.url)
    PACTOS.mkdir(parents=True, exist_ok=True)
    pacto.write_file(PACTOS, overwrite=True)


def _llamar(nucleo_url: str, operacion):
    async def ejecutar():
        async with httpx.AsyncClient(base_url=nucleo_url) as http:
            return await operacion(ClienteMsCotizacion(http))

    return asyncio.run(ejecutar())


def test_catalogo_de_un_ramo(nucleo_url):
    producto = _llamar(nucleo_url, lambda c: c.obtener_producto("soat-motocicleta"))

    vista = _catalogo_salida(producto, "SOAT")
    assert vista["moneda"] == "COP"
    assert {d["tipo"] for d in vista["datosRiesgo"]} == {"rango", "valores"}


def test_catalogo_de_un_ramo_sin_producto(nucleo_url):
    with pytest.raises(RecursoNoEncontrado):
        _llamar(nucleo_url, lambda c: c.obtener_producto("no-existe"))


def _cotizar(cliente: ClienteMsCotizacion, clave: str, datos_riesgo: dict):
    return cliente.cotizar(
        idempotency_key=clave,
        usuario_id=UUID("0b6f3c1e-2d4a-5b7c-8d9e-0f1a2b3c4d5e"),
        socio_id=UUID("1c7a4d2f-3e5b-5c8d-9e0f-1a2b3c4d5e6f"),
        consentimiento_id=UUID("2d8b5e3a-4f6c-5d9e-8f1a-2b3c4d5e6f7a"),
        producto="soat-motocicleta",
        canal="web",
        datos_riesgo=datos_riesgo,
    )


def test_cotizacion(nucleo_url):
    datos_riesgo = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}
    datos = _llamar(nucleo_url, lambda c: _cotizar(c, "clave-cotizacion-0001", datos_riesgo))

    vista = _cotizacion_salida(datos, "SOAT")
    assert vista["cotizacionId"] == COTIZACION_ID
    assert Decimal(vista["prima"]) == Decimal(vista["primaNeta"]) + Decimal(vista["expedicion"])


def test_cotizacion_con_dato_fuera_de_rango_es_rechazo_del_nucleo(nucleo_url):
    with pytest.raises(RechazoDelNucleo) as rechazo:
        _llamar(nucleo_url, lambda c: _cotizar(c, "clave-cotizacion-0002", DATOS_RIESGO_FUERA_DE_RANGO))

    assert (rechazo.value.status, rechazo.value.codigo) == (422, "dato_riesgo_fuera_de_rango")


def test_reconsulta_de_una_cotizacion(nucleo_url):
    datos = _llamar(nucleo_url, lambda c: c.reconsultar(COTIZACION_ID))

    vista = _cotizacion_salida(datos, datos["producto"])
    assert (vista["cotizacionId"], vista["ramo"]) == (COTIZACION_ID, "soat-motocicleta")


def _aceptar(cliente: ClienteMsCotizacion, clave: str):
    return cliente.aceptar_oferta(
        cotizacion_id=COTIZACION_ID,
        idempotency_key=clave,
        perfil_id=UUID("3e9c6f4b-5a7d-5e0f-9a2b-3c4d5e6f7a8b"),
        score=Decimal("0.5000"),
    )


def test_aceptacion_aceptada_entrega_lo_necesario_para_cobrar_y_emitir(nucleo_url):
    aceptacion = _llamar(nucleo_url, lambda c: _aceptar(c, "clave-aceptacion-0001"))

    assert aceptacion["decision"].upper() == "ACEPTADA"
    assert (UUID(aceptacion["oferta_id"]), UUID(aceptacion["cotizacion_id"])) == (UUID(OFERTA_ID), UUID(COTIZACION_ID))
    assert Decimal(str(aceptacion["prima"])) > 0
    assert aceptacion["moneda"] == "COP"


def test_aceptacion_rechazada_entrega_el_motivo(nucleo_url):
    aceptacion = _llamar(nucleo_url, lambda c: _aceptar(c, "clave-aceptacion-0002"))

    assert aceptacion["decision"].upper() == "RECHAZADA"
    assert aceptacion["motivo"]


def test_cotizacion_de_una_oferta_emitida(nucleo_url):
    cotizacion = _llamar(nucleo_url, lambda c: c.reconsultar_por_oferta(UUID(OFERTA_ID)))

    assert cotizacion["producto"] == "soat-motocicleta"
    assert (cotizacion["moneda"], float(cotizacion["prima"])) == ("COP", 140500.0)
