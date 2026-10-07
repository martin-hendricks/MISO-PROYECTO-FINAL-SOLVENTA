from app.domain.errores import ProductoNoEncontrado
from app.main import estado_http


def test_producto_no_encontrado_se_traduce_a_404():
    assert estado_http(ProductoNoEncontrado("x")) == 404


def test_health_metrics_y_correlacion(client):
    salud = client.get("/health", headers={"X-Correlation-Id": "c-123"})

    assert salud.json() == {"status": "ok"}
    assert salud.headers["X-Correlation-Id"] == "c-123"
    assert "http_request_duration_seconds" in client.get("/metrics").text
