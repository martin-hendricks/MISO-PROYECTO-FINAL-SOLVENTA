from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

CABECERAS = {"Idempotency-Key": "clave-de-prueba-0001"}


def _payload(**overrides):
    base = {
        "usuario_id": str(uuid4()),
        "socio_id": str(uuid4()),
        "consentimiento_id": str(uuid4()),
        "producto": "soat-motocicleta",
        "canal": "app-socio",
        "datos_riesgo": {"cilindraje_cc": 150, "modelo_anio": 2022, "ciudad_circulacion": "bogota"},
    }
    base.update(overrides)
    return base


def test_solicitud_valida_devuelve_oferta_en_el_mismo_flujo(client):
    respuesta = client.post("/v1/cotizaciones", json=_payload(), headers=CABECERAS)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert "cotizacion_id" in cuerpo
    assert cuerpo["estado"] == "cotizada"
    assert Decimal(cuerpo["prima"]) == Decimal(cuerpo["prima_neta"]) + Decimal(cuerpo["gastos_expedicion"])
    assert "moneda" in cuerpo and "vence_en" in cuerpo
    assert cuerpo["factor_riesgo_origen"] in ("real", "respaldo")


def test_reintento_con_misma_clave_devuelve_200(client):
    client.post("/v1/cotizaciones", json=_payload(), headers=CABECERAS)
    respuesta = client.post("/v1/cotizaciones", json=_payload(), headers=CABECERAS)

    assert respuesta.status_code == 200


def test_dato_riesgo_fuera_de_rango_devuelve_422_sin_cotizacion_id(client):
    payload = _payload(datos_riesgo={"cilindraje_cc": 9999, "modelo_anio": 2022, "ciudad_circulacion": "bogota"})

    respuesta = client.post("/v1/cotizaciones", json=payload, headers=CABECERAS)

    assert respuesta.status_code == 422
    cuerpo = respuesta.json()
    assert "cotizacion_id" not in cuerpo
    assert cuerpo["codigo"] == "dato_riesgo_fuera_de_rango"


def test_producto_inexistente_devuelve_404(client):
    respuesta = client.post("/v1/cotizaciones", json=_payload(producto="no-existe"), headers=CABECERAS)

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "producto_no_encontrado"


def test_falta_header_idempotency_key_devuelve_422(client):
    respuesta = client.post("/v1/cotizaciones", json=_payload())

    assert respuesta.status_code == 422


def test_get_cotizacion_devuelve_404_si_no_existe(client):
    respuesta = client.get(f"/v1/cotizaciones/{uuid4()}")

    assert respuesta.status_code == 404
    cuerpo = respuesta.json()
    assert set(cuerpo) == {"codigo", "mensaje"}


def test_get_cotizacion_dos_veces_devuelve_el_mismo_cuerpo(client):
    creada = client.post("/v1/cotizaciones", json=_payload(), headers=CABECERAS).json()
    cotizacion_id = creada["cotizacion_id"]

    primera = client.get(f"/v1/cotizaciones/{cotizacion_id}")
    segunda = client.get(f"/v1/cotizaciones/{cotizacion_id}")

    assert primera.status_code == 200
    assert primera.json() == segunda.json()


def test_get_cotizacion_vencida_devuelve_vencida_true(client, almacen):
    creada = client.post("/v1/cotizaciones", json=_payload(), headers=CABECERAS).json()
    oferta_id = next(iter(almacen.ofertas))
    almacen.ofertas[oferta_id].vence_en = datetime.now(UTC) - timedelta(seconds=1)

    respuesta = client.get(f"/v1/cotizaciones/{creada['cotizacion_id']}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["vencida"] is True
    assert Decimal(cuerpo["prima"]) == Decimal(creada["prima"])
