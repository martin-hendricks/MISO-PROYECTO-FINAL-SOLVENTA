from pathlib import Path
from uuid import uuid4

MIGRACION = Path(__file__).resolve().parents[1] / "db" / "11_ms_cotizacion_consentimiento_opcional.sql"


def _payload(**cambios) -> dict:
    base = {
        "usuario_id": str(uuid4()),
        "socio_id": str(uuid4()),
        "producto": "soat-motocicleta",
        "canal": "app-socio",
        "datos_riesgo": {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"},
    }
    base.update(cambios)
    return base


def _evento_recibida(almacen) -> dict:
    eventos = [e for e in almacen.eventos if e.tipo == "SolicitudCotizacionRecibida"]
    assert len(eventos) == 1
    return eventos[0].payload


def test_cotiza_sin_consentimiento_y_lo_marca_pendiente(client, almacen):
    respuesta = client.post("/v1/cotizaciones", json=_payload(), headers={"Idempotency-Key": "sin-consent-0001"})

    assert respuesta.status_code == 201
    payload = _evento_recibida(almacen)
    assert payload["canal"] == "app-socio"
    assert payload["consentimiento_pendiente"] is True


def test_con_consentimiento_cotiza_igual_y_no_queda_pendiente(client, almacen):
    respuesta = client.post(
        "/v1/cotizaciones",
        json=_payload(consentimiento_id=str(uuid4()), canal="web"),
        headers={"Idempotency-Key": "con-consent-0001"},
    )

    assert respuesta.status_code == 201
    payload = _evento_recibida(almacen)
    assert payload["canal"] == "web"
    assert payload["consentimiento_pendiente"] is False


def test_el_evento_conserva_sus_campos_anteriores(client, almacen):
    usuario_id = str(uuid4())

    client.post("/v1/cotizaciones", json=_payload(usuario_id=usuario_id), headers={"Idempotency-Key": "campos-0001"})

    payload = _evento_recibida(almacen)
    assert payload["producto"] == "soat-motocicleta"
    assert payload["usuario_id"] == usuario_id
    assert "solicitud_id" in payload


def test_la_migracion_permite_consentimiento_nulo_sin_tocar_filas():
    texto = MIGRACION.read_text(encoding="utf-8")

    assert "ALTER COLUMN consentimiento_id DROP NOT NULL" in texto
    assert "UPDATE" not in texto.upper()
    assert "DELETE" not in texto.upper()
