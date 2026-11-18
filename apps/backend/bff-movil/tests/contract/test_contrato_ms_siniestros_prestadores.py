"""Pacto bff-movil -> ms-siniestros (006): ciudades del país y prestadores del área visible del mapa.

Cada test pasa la respuesta del mock por la misma traducción que usa la ruta móvil.
"""

from pathlib import Path

import pytest

from app.clients.nucleo import ClienteNucleo, RechazoNucleo
from app.routers.cliente import _bordes, _respuesta_prestadores

pact_v3 = pytest.importorskip("pact.v3")
match = pact_v3.match

pytestmark = pytest.mark.contract

PACTOS = Path(__file__).resolve().parents[2] / "pacts"
DECIMAL = r"^-?\d+(\.\d+)?$"

CHAPINERO = {"norte": "4.66", "sur": "4.62", "este": "-74.05", "oeste": "-74.08", "limite": "500"}
AREA_INVERTIDA = {**CHAPINERO, "norte": "4.6", "sur": "4.7"}

PRESTADOR = {
    "id": match.str("PRE-BOG-06"),
    "nombre": match.str("Taller Moto Chapinero"),
    "tipo": match.str("taller-motos"),
    "ramos": match.each_like("soat-motocicleta"),
    "direccion": match.str("Cra 13 # 54-20"),
    "ciudad": match.str("Bogotá"),
    "pais": match.regex("CO", regex=r"^[A-Z]{2}$"),
    "barrio": match.str("Chapinero"),
    "lat": match.regex("4.635500", regex=DECIMAL),
    "lng": match.regex("-74.065500", regex=DECIMAL),
    "telefono": match.str("601 555 0112"),
    "horario": match.str("Lun–Sáb 7:00–19:00"),
}


@pytest.fixture(scope="module")
def nucleo():
    pacto = pact_v3.Pact("bff-movil", "ms-siniestros").with_specification("V4")
    (
        pacto.upon_receiving("las ciudades con prestadores activos de Perú para el cliente móvil")
        .given("hay prestadores sembrados en cuatro países")
        .with_request("GET", "/v1/prestadores/ciudades")
        .with_query_parameter("pais", "PE")
        .with_query_parameter("con_prestadores", "true")
        .will_respond_with(200)
        .with_body(
            {
                "pais": "PE",
                "ciudades": match.each_like(
                    {
                        "nombre": match.str("Lima"),
                        "lat": match.regex("-12.046400", regex=DECIMAL),
                        "lng": match.regex("-77.042800", regex=DECIMAL),
                        "zoom": match.int(11),
                        "prestadores": match.int(5),
                    }
                ),
            }
        )
    )
    (
        pacto.upon_receiving("los prestadores del área visible de Chapinero para el cliente móvil")
        .given("hay prestadores sembrados en cuatro países")
        .with_request("GET", "/v1/prestadores")
        .with_query_parameters(CHAPINERO)
        .will_respond_with(200)
        .with_body(
            {
                "centro": None,
                "radio_km": None,
                "truncado": match.bool(False),
                "prestadores": match.each_like(PRESTADOR),
            }
        )
    )
    (
        pacto.upon_receiving("un área visible móvil con el sur por encima del norte")
        .with_request("GET", "/v1/prestadores")
        .with_query_parameters(AREA_INVERTIDA)
        .will_respond_with(422)
        .with_body({"codigo": "area_invalida", "mensaje": match.str("El área visible no es válida.")})
    )
    with pacto.serve() as servidor:
        yield ClienteNucleo({"ms-siniestros": str(servidor.url)})
    PACTOS.mkdir(parents=True, exist_ok=True)
    pacto.write_file(PACTOS, overwrite=True)


def test_ciudades_del_pais(nucleo):
    cuerpo = nucleo.ciudades_prestadores("PE")

    assert cuerpo["pais"] == "PE"
    assert {"nombre", "lat", "lng", "zoom", "prestadores"} <= set(cuerpo["ciudades"][0])


def test_prestadores_del_area_visible(nucleo):
    cuerpo = nucleo.prestadores(**_bordes(4.66, 4.62, -74.05, -74.08))

    vista = _respuesta_prestadores(cuerpo)
    assert vista["truncado"] is False
    assert vista["prestadores"][0]["pais"] == "CO"


def test_area_invertida_llega_como_422_con_el_codigo(nucleo):
    with pytest.raises(RechazoNucleo) as rechazo:
        nucleo.prestadores(**_bordes(4.6, 4.7, -74.05, -74.08))

    assert (rechazo.value.status_code, rechazo.value.codigo) == (422, "area_invalida")
