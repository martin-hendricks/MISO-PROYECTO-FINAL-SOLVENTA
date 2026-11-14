import logging

from fastapi.testclient import TestClient

from app.main import app
from app.routers.identidad import VerificadorPruebaDeVida, obtener_verificador

JPEG = b"\xff\xd8\xff\xd9"
LIMITE = 10 * 1024 * 1024


def _foto(contenido: bytes, tipo: str):
    return {"foto": ("selfie.jpg", contenido, tipo)}


def test_jpeg_valido_es_ok(client):
    response = client.post("/v1/identidad/prueba-de-vida", files=_foto(JPEG, "image/jpeg"))
    assert response.status_code == 200
    assert response.json() == {"resultado": "ok"}
    assert response.request.headers.get("authorization") is None


def test_vacio_otro_tipo_o_grande_es_no(client):
    vacio = client.post("/v1/identidad/prueba-de-vida", files=_foto(b"", "image/jpeg"))
    png = client.post("/v1/identidad/prueba-de-vida", files=_foto(JPEG, "image/png"))
    grande = client.post(
        "/v1/identidad/prueba-de-vida",
        files=_foto(b"x" * (LIMITE + 1), "image/jpeg"),
    )
    assert vacio.status_code == 200 and vacio.json()["resultado"] == "no"
    assert png.status_code == 200 and png.json()["resultado"] == "no"
    assert grande.status_code == 200 and grande.json()["resultado"] == "no"


def test_sin_archivo_es_422(client):
    assert client.post("/v1/identidad/prueba-de-vida").status_code == 422


def test_verificador_caido_es_503(client: TestClient):
    class Roto(VerificadorPruebaDeVida):
        def evaluar(self, contenido: bytes, tipo: str | None) -> str:
            raise RuntimeError("caido")

    app.dependency_overrides[obtener_verificador] = lambda: Roto()
    try:
        response = client.post("/v1/identidad/prueba-de-vida", files=_foto(JPEG, "image/jpeg"))
    finally:
        app.dependency_overrides.clear()
    assert response.status_code == 503
    assert response.json()["detail"] == "servicio_no_disponible"


def test_sin_v1_no_existe_y_el_prefijo_movil_si(client):
    assert client.post("/identidad/prueba-de-vida", files=_foto(JPEG, "image/jpeg")).status_code == 404
    movil = client.post("/bff-movil/v1/identidad/prueba-de-vida", files=_foto(JPEG, "image/jpeg"))
    assert movil.status_code == 200
    assert movil.json()["resultado"] == "ok"


def test_correlacion_no_cambia_la_respuesta_y_los_bytes_no_se_loguean(client, caplog):
    caplog.set_level(logging.DEBUG)
    marca = b"bytes-secretos-de-la-foto"
    response = client.post(
        "/v1/identidad/prueba-de-vida",
        files=_foto(marca, "image/jpeg"),
        headers={"X-Correlation-Id": "corr-1"},
    )
    assert response.status_code == 200
    assert "bytes-secretos-de-la-foto" not in caplog.text
