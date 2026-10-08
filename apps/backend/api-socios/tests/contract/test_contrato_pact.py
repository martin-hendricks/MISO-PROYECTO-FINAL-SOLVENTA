"""Contrato Pact (CDC) de :APISocios con ms-cotizacion para el catálogo (HU-2 / SOLV-95, PI-01).

api-socios es el consumidor: este test genera el pacto en api-socios/pacts/ y
ms-cotizacion lo verifica en tests/contract/. Correr con `pytest -m contract`
(requiere `pip install -e ".[test,contract]"`).
"""

from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from app.api.v1.schemas import ProductoVista
from app.clients.base import RecursoNoEncontrado
from app.clients.ms_cotizacion import ClienteMsCotizacion

pact_v3 = pytest.importorskip("pact.v3")
match = pact_v3.match

pytestmark = pytest.mark.contract

PACTOS = Path(__file__).resolve().parents[2] / "pacts"
DECIMAL = r"^-?\d+(\.\d+)?$"

PRODUCTO = {
    "producto": match.str("soat-motocicleta"),
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


@pytest.fixture(scope="module")
def nucleo_url():
    pacto = pact_v3.Pact("api-socios", "ms-cotizacion").with_specification("V4")
    (
        pacto.upon_receiving("una consulta del catálogo de productos")
        .with_request("GET", "/v1/productos")
        .will_respond_with(200)
        .with_body(match.each_like(PRODUCTO))
    )
    (
        pacto.upon_receiving("una consulta de soat-motocicleta")
        .with_request("GET", "/v1/productos/soat-motocicleta")
        .will_respond_with(200)
        .with_body(PRODUCTO)
    )
    (
        pacto.upon_receiving("una consulta de un producto que no existe")
        .with_request("GET", "/v1/productos/no-existe")
        .will_respond_with(404)
        .with_body({"codigo": "producto_no_encontrado", "mensaje": match.str("Producto 'no-existe' no existe")})
    )
    with pacto.serve() as servidor:
        yield str(servidor.url)
    PACTOS.mkdir(parents=True, exist_ok=True)
    pacto.write_file(PACTOS, overwrite=True)


async def test_consulta_del_catalogo(nucleo_url):
    async with httpx.AsyncClient(base_url=nucleo_url) as http:
        productos = await ClienteMsCotizacion(http).listar_productos()

    vista = ProductoVista.desde_nucleo(productos[0])
    assert (vista.codigo, vista.moneda) == ("soat-motocicleta", "COP")


async def test_consulta_de_un_producto_por_codigo(nucleo_url):
    async with httpx.AsyncClient(base_url=nucleo_url) as http:
        producto = await ClienteMsCotizacion(http).obtener_producto("soat-motocicleta")

    vista = ProductoVista.desde_nucleo(producto)
    assert vista.coberturas[0].limite.valor == Decimal("800")
    assert {d.tipo for d in vista.datos_riesgo} == {"rango", "valores"}


async def test_consulta_de_un_producto_inexistente(nucleo_url):
    async with httpx.AsyncClient(base_url=nucleo_url) as http:
        with pytest.raises(RecursoNoEncontrado):
            await ClienteMsCotizacion(http).obtener_producto("no-existe")
