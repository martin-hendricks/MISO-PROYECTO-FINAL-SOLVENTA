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


def test_solicitud_valida_devuelve_cotizacion_id_201(client):
    respuesta = client.post("/v1/cotizaciones", json=_payload(), headers=CABECERAS)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert "cotizacion_id" in cuerpo
    assert cuerpo["estado"] == "recibida"


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


def test_producto_inexistente_devuelve_422(client):
    respuesta = client.post("/v1/cotizaciones", json=_payload(producto="no-existe"), headers=CABECERAS)

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "producto_no_encontrado"


def test_falta_header_idempotency_key_devuelve_422(client):
    respuesta = client.post("/v1/cotizaciones", json=_payload())

    assert respuesta.status_code == 422
