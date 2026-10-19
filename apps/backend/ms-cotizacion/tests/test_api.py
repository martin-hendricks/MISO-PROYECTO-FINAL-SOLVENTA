import pytest

from app.api.v1.schemas import DatoRiesgoSalida
from app.domain.errores import ProductoNoEncontrado
from app.main import estado_http


def test_producto_no_encontrado_se_traduce_a_404():
    assert estado_http(ProductoNoEncontrado("x")) == 404


def test_consultar_producto_por_codigo(client):
    respuesta = client.get("/v1/productos/soat-motocicleta")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert (cuerpo["producto"], cuerpo["moneda"]) == ("soat-motocicleta", "COP")
    assert cuerpo["coberturas"][0] == {
        "codigo": "gastos_medicos",
        "nombre": "Gastos médicos",
        "limite": "800",
        "unidad_limite": "SMLDV",
    }
    assert {d["nombre"]: d for d in cuerpo["datos_riesgo"]}["ciudad_circulacion"] == {
        "nombre": "ciudad_circulacion",
        "tipo": "valores",
        "minimo": None,
        "maximo": None,
        "valores": ["bogota", "medellin", "cali", "barranquilla", "bucaramanga"],
    }


def test_listar_productos(client):
    respuesta = client.get("/v1/productos")

    assert respuesta.status_code == 200
    assert [p["producto"] for p in respuesta.json()] == ["soat-motocicleta"]


def test_producto_inexistente_responde_404_tipificado(client):
    respuesta = client.get("/v1/productos/soat-automovil")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "producto_no_encontrado"


def test_dato_de_riesgo_sin_representacion_publica_falla():
    class DatoDesconocido:
        def valido(self, valor):
            return True

        def describir_rango(self):
            return ""

    with pytest.raises(TypeError, match="DatoDesconocido"):
        DatoRiesgoSalida.desde("x", DatoDesconocido())


def test_health_metrics_y_correlacion(client):
    salud = client.get("/health", headers={"X-Correlation-Id": "c-123"})

    assert salud.json() == {"status": "ok"}
    assert salud.headers["X-Correlation-Id"] == "c-123"
    assert "http_request_duration_seconds" in client.get("/metrics").text
