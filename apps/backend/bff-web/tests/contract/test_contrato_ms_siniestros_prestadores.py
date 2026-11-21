"""Pacto bff-web -> ms-siniestros (006): ciudades del país y prestadores del área visible del mapa.

Cada test pasa la respuesta del mock por la misma traducción que usa la ruta web.
"""

import asyncio
from pathlib import Path

import httpx
import pytest

from app.clients.base import RechazoDelNucleo
from app.clients.ms_siniestros import ClienteMsSiniestros
from app.routers.prestadores import _bordes, _ciudades, _fila_cliente

pact_v3 = pytest.importorskip("pact.v3")
match = pact_v3.match

pytestmark = pytest.mark.contract

PACTOS = Path(__file__).resolve().parents[2] / "pacts"
DECIMAL = r"^-?\d+(\.\d+)?$"

CHAPINERO = {"norte": "4.66", "sur": "4.62", "este": "-74.05", "oeste": "-74.08", "limite": "500"}
AREA_INVERTIDA = {**CHAPINERO, "norte": "4.6", "sur": "4.7"}

CIUDAD = {
    "nombre": match.str("Bogotá"),
    "lat": match.regex("4.609700", regex=DECIMAL),
    "lng": match.regex("-74.081700", regex=DECIMAL),
    "zoom": match.int(12),
    "prestadores": match.int(30),
}

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
def nucleo_url():
    pacto = pact_v3.Pact("bff-web", "ms-siniestros").with_specification("V4")
    (
        pacto.upon_receiving("las ciudades de Colombia con prestadores activos para el cliente web")
        .given("hay prestadores sembrados en cuatro países")
        .with_request("GET", "/v1/prestadores/ciudades")
        .with_query_parameters({"pais": "CO", "con_prestadores": "true"})
        .will_respond_with(200)
        .with_body({"pais": "CO", "ciudades": match.each_like(CIUDAD)})
    )
    (
        pacto.upon_receiving("todas las ciudades de México para el operador")
        .given("hay prestadores sembrados en cuatro países")
        .with_request("GET", "/v1/prestadores/ciudades")
        .with_query_parameters({"pais": "MX", "con_prestadores": "false"})
        .will_respond_with(200)
        .with_body({"pais": "MX", "ciudades": match.each_like({**CIUDAD, "nombre": match.str("Ciudad de México")})})
    )
    (
        pacto.upon_receiving("los prestadores del área visible de Chapinero para el cliente web")
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
        pacto.upon_receiving("un área visible web con el sur por encima del norte")
        .with_request("GET", "/v1/prestadores")
        .with_query_parameters(AREA_INVERTIDA)
        .will_respond_with(422)
        .with_body({"codigo": "area_invalida", "mensaje": match.str("El área visible no es válida.")})
    )
    with pacto.serve() as servidor:
        yield str(servidor.url)
    PACTOS.mkdir(parents=True, exist_ok=True)
    pacto.write_file(PACTOS, overwrite=True)


def _llamar(nucleo_url: str, operacion):
    async def ejecutar():
        async with httpx.AsyncClient(base_url=nucleo_url) as http:
            return await operacion(ClienteMsSiniestros(http))

    return asyncio.run(ejecutar())


def test_ciudades_del_cliente(nucleo_url):
    vista = _ciudades(_llamar(nucleo_url, lambda c: c.ciudades_prestadores("CO", True)))

    assert vista["pais"] == "CO"
    assert vista["ciudades"][0]["zoom"] == 12


def test_ciudades_del_operador(nucleo_url):
    vista = _ciudades(_llamar(nucleo_url, lambda c: c.ciudades_prestadores("MX", False)))

    assert vista["pais"] == "MX"


def test_prestadores_del_area_visible(nucleo_url):
    cuerpo = _llamar(nucleo_url, lambda c: c.prestadores(**_bordes(4.66, 4.62, -74.05, -74.08)))

    assert cuerpo["truncado"] is False
    assert _fila_cliente(cuerpo["prestadores"][0])["pais"] == "CO"


def test_area_invertida_llega_como_422_con_el_codigo(nucleo_url):
    with pytest.raises(RechazoDelNucleo) as rechazo:
        _llamar(nucleo_url, lambda c: c.prestadores(**_bordes(4.6, 4.7, -74.05, -74.08)))

    assert (rechazo.value.status, rechazo.value.codigo) == (422, "area_invalida")
