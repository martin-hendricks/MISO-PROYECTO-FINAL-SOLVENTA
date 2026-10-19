import httpx

from .conftest import PRODUCTO

PRODUCTO_PUBLICADO = {
    "codigo": "soat-motocicleta",
    "nombre": "SOAT motocicleta",
    "moneda": "COP",
    "coberturas": [
        {"codigo": "gastos_medicos", "nombre": "Gastos médicos", "limite": {"valor": "800.00", "unidad": "SMLDV"}},
        {"codigo": "muerte", "nombre": "Muerte y gastos funerarios", "limite": {"valor": "750.00", "unidad": "SMLDV"}},
    ],
    "datosRiesgo": [
        {"nombre": "cilindraje_cc", "tipo": "rango", "minimo": "50", "maximo": "1800"},
        {"nombre": "ciudad_circulacion", "tipo": "valores", "valores": ["bogota", "cali"]},
    ],
}


def test_socio_consulta_el_catalogo(client):
    respuesta = client.get("/v1/catalogo")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"productos": [PRODUCTO_PUBLICADO]}


def test_socio_consulta_un_producto_por_codigo(client, nucleo):
    respuesta = client.get("/v1/catalogo/soat-motocicleta")

    assert respuesta.status_code == 200
    assert respuesta.json() == PRODUCTO_PUBLICADO
    assert nucleo.peticiones[-1].headers["X-Correlation-Id"] == "corr-test"


def test_la_respuesta_no_expone_el_modelo_interno(client):
    cuerpo = client.get("/v1/catalogo/soat-motocicleta").json()

    assert "producto" not in cuerpo and "datos_riesgo" not in cuerpo
    assert "campoInternoDelNucleo" not in cuerpo and "campo_interno_del_nucleo" not in cuerpo
    assert "unidad_limite" not in cuerpo["coberturas"][0]


def test_campo_nuevo_del_nucleo_no_rompe_el_contrato(client, nucleo):
    con_campo_nuevo = {**PRODUCTO, "vigencia": "anual", "coberturas": [{**PRODUCTO["coberturas"][0], "deducible": "0"}]}
    nucleo.respuestas[("GET", "/v1/productos/soat-motocicleta")] = lambda _: httpx.Response(200, json=con_campo_nuevo)

    respuesta = client.get("/v1/catalogo/soat-motocicleta")

    assert respuesta.status_code == 200
    assert respuesta.json()["coberturas"] == PRODUCTO_PUBLICADO["coberturas"][:1]


def test_producto_inexistente_es_404(client):
    respuesta = client.get("/v1/catalogo/soat-automovil")

    assert respuesta.status_code == 404
    assert respuesta.json() == {"codigo": "no_encontrado", "mensaje": "No existe"}


def test_nucleo_caido_se_enmascara_como_503(client, nucleo):
    def caido(request):
        raise httpx.ConnectError("conexión rechazada", request=request)

    nucleo.respuestas[("GET", "/v1/productos")] = caido
    respuesta = client.get("/v1/catalogo")

    assert respuesta.status_code == 503
    assert "ms-cotizacion" not in respuesta.text


def test_error_500_del_nucleo_tambien_es_503(client, nucleo):
    nucleo.respuestas[("GET", "/v1/productos")] = lambda _: httpx.Response(500, text="Traceback")
    assert client.get("/v1/catalogo").status_code == 503


def test_rechazo_de_negocio_del_nucleo_se_propaga(client, nucleo):
    nucleo.respuestas[("GET", "/v1/productos/soat-motocicleta")] = lambda _: httpx.Response(
        422, json={"codigo": "producto_suspendido", "mensaje": "Producto suspendido"}
    )

    respuesta = client.get("/v1/catalogo/soat-motocicleta")

    assert respuesta.status_code == 422
    assert respuesta.json() == {"codigo": "producto_suspendido", "mensaje": "Producto suspendido"}


def test_solo_lectura(client):
    assert client.post("/v1/catalogo", json={}).status_code == 405
    assert client.put("/v1/catalogo/soat-motocicleta", json={}).status_code == 405
    assert client.delete("/v1/catalogo/soat-motocicleta").status_code == 405
