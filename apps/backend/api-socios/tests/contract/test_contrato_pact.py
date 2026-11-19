from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from app.api.v1.rutas import CANAL_SOCIO
from app.api.v1.schemas import CotizacionVista, ProductoVista
from app.clients.base import RecursoNoEncontrado
from app.clients.ms_cotizacion import ClienteMsCotizacion
from app.clients.token_servicio import token_de_socio

pact_v3 = pytest.importorskip("pact.v3")
match = pact_v3.match

pytestmark = pytest.mark.contract

PACTOS = Path(__file__).resolve().parents[2] / "pacts"
DECIMAL = r"^-?\d+(\.\d+)?$"
MONEDA = r"^[A-Z]{3}$"
FECHA_ISO = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
JWT = r"^Bearer [A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$"

SOCIO_ID = "4fa85f64-5717-4562-b3fc-2c963f66afa6"
USUARIO_ID = "0b6f3c1e-2d4a-4b7c-8d9e-0f1a2b3c4d5e"
CONSENTIMIENTO_ID = "2d8b5e3a-4f6c-4d9e-8f1a-2b3c4d5e6f7a"
COTIZACION_ID = "6f1c2b9e-8d4a-4f7b-9c3e-1a2b3c4d5e6f"
COTIZACION_AJENA = "7a2d3c0f-9e5b-4a8c-8d4f-2b3c4d5e6f70"
CLAVE_CON_CONSENTIMIENTO = f"{SOCIO_ID}:clave-socio-0001"
CLAVE_SIN_CONSENTIMIENTO = f"{SOCIO_ID}:clave-socio-0002"
SECRETO = "secreto-del-pacto"
DATOS_RIESGO = {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"}

TOKEN_EJEMPLO = token_de_socio(SECRETO, SOCIO_ID, ahora=datetime(2026, 1, 1, tzinfo=UTC))
AUTORIZACION = match.regex(f"Bearer {TOKEN_EJEMPLO}", regex=JWT)

COTIZACION = {
    "cotizacion_id": match.uuid(COTIZACION_ID),
    "estado": match.str("cotizada"),
    "producto": match.str("soat-motocicleta"),
    "prima": match.regex("140500.00", regex=DECIMAL),
    "prima_neta": match.regex("132500.00", regex=DECIMAL),
    "gastos_expedicion": match.regex("8000.00", regex=DECIMAL),
    "moneda": match.regex("COP", regex=MONEDA),
    "vence_en": match.regex("2026-10-30T13:00:00Z", regex=FECHA_ISO),
}

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


def _solicitud(consentimiento) -> dict:
    return {
        "usuario_id": match.uuid(USUARIO_ID),
        "socio_id": SOCIO_ID,
        "consentimiento_id": consentimiento,
        "producto": match.str("soat-motocicleta"),
        "canal": CANAL_SOCIO,
        "datos_riesgo": match.like(DATOS_RIESGO),
    }


def _cliente(http: httpx.AsyncClient) -> ClienteMsCotizacion:
    return ClienteMsCotizacion(http, token=token_de_socio(SECRETO, SOCIO_ID))


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
    for descripcion, clave, consentimiento in (
        ("una cotización del socio con consentimiento vigente", CLAVE_CON_CONSENTIMIENTO, match.uuid(CONSENTIMIENTO_ID)),
        ("una cotización del socio sin consentimiento", CLAVE_SIN_CONSENTIMIENTO, None),
    ):
        (
            pacto.upon_receiving(descripcion)
            .given("un socio autenticado", parameters={"socio_id": SOCIO_ID})
            .with_request("POST", "/v1/cotizaciones")
            .with_header("Authorization", AUTORIZACION)
            .with_header("Idempotency-Key", clave)
            .with_body(_solicitud(consentimiento), content_type="application/json")
            .will_respond_with(201)
            .with_body(COTIZACION)
        )
    (
        pacto.upon_receiving("la reconsulta de una cotización del socio")
        .given(
            "existe una cotización vigente del socio",
            parameters={"cotizacion_id": COTIZACION_ID, "socio_id": SOCIO_ID},
        )
        .with_request("GET", f"/v1/cotizaciones/{COTIZACION_ID}")
        .with_header("Authorization", AUTORIZACION)
        .will_respond_with(200)
        .with_body({**COTIZACION, "vencida": match.bool(False)})
    )
    (
        pacto.upon_receiving("la reconsulta de una cotización de otro socio")
        .given(
            "existe una cotización de otro socio",
            parameters={"cotizacion_id": COTIZACION_AJENA, "socio_id": SOCIO_ID},
        )
        .with_request("GET", f"/v1/cotizaciones/{COTIZACION_AJENA}")
        .with_header("Authorization", AUTORIZACION)
        .will_respond_with(404)
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


async def _cotizar(nucleo_url: str, clave: str, consentimiento_id: str | None) -> tuple[int, dict]:
    async with httpx.AsyncClient(base_url=nucleo_url) as http:
        return await _cliente(http).cotizar(
            {
                "usuario_id": USUARIO_ID,
                "socio_id": SOCIO_ID,
                "consentimiento_id": consentimiento_id,
                "producto": "soat-motocicleta",
                "canal": CANAL_SOCIO,
                "datos_riesgo": DATOS_RIESGO,
            },
            clave,
        )


async def test_cotizacion_del_socio_con_consentimiento_vigente(nucleo_url):
    estado, datos = await _cotizar(nucleo_url, CLAVE_CON_CONSENTIMIENTO, CONSENTIMIENTO_ID)

    vista = CotizacionVista.desde_nucleo(datos, consentimiento_pendiente=False)
    assert (estado, vista.cotizacion_id, vista.moneda) == (201, COTIZACION_ID, "COP")


async def test_cotizacion_del_socio_sin_consentimiento(nucleo_url):
    estado, datos = await _cotizar(nucleo_url, CLAVE_SIN_CONSENTIMIENTO, None)

    vista = CotizacionVista.desde_nucleo(datos, consentimiento_pendiente=True)
    assert (estado, vista.estado, vista.consentimiento_pendiente) == (201, "cotizada", True)


async def test_reconsulta_de_una_cotizacion_del_socio(nucleo_url):
    async with httpx.AsyncClient(base_url=nucleo_url) as http:
        datos = await _cliente(http).obtener_cotizacion(COTIZACION_ID)

    vista = CotizacionVista.desde_nucleo(datos)
    assert (vista.cotizacion_id, vista.producto, vista.vencida) == (COTIZACION_ID, "soat-motocicleta", False)


async def test_reconsulta_de_una_cotizacion_de_otro_socio(nucleo_url):
    async with httpx.AsyncClient(base_url=nucleo_url) as http:
        with pytest.raises(RecursoNoEncontrado):
            await _cliente(http).obtener_cotizacion(COTIZACION_AJENA)
