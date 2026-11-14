def _otorgar(client, cliente_id="cliente-1"):
    return client.post("/v1/consentimientos", json={"cliente_id": cliente_id})


def test_otorgar_201_la_primera_vez(client):
    respuesta = _otorgar(client)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["cliente_id"] == "cliente-1"
    assert cuerpo["vigente"] is True
    assert cuerpo["revocado_en"] is None


def test_otorgar_200_en_el_reintento_mismo_id(client):
    primero = _otorgar(client)
    reintento = _otorgar(client)

    assert primero.status_code == 201
    assert reintento.status_code == 200
    assert reintento.json()["id"] == primero.json()["id"]


def test_otorgar_cliente_id_vacio_es_422(client):
    respuesta = client.post("/v1/consentimientos", json={"cliente_id": ""})
    assert respuesta.status_code == 422


def test_consultar_vigente(client):
    creado = _otorgar(client).json()

    respuesta = client.get("/v1/consentimientos/cliente-1")

    assert respuesta.status_code == 200
    assert respuesta.json() == creado


def test_consultar_sin_consentimiento_es_404(client):
    respuesta = client.get("/v1/consentimientos/cliente-sin-consentimiento")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_revocar_200_y_queda_no_vigente(client):
    _otorgar(client)

    respuesta = client.delete("/v1/consentimientos/cliente-1")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["vigente"] is False
    assert cuerpo["revocado_en"] is not None


def test_revocar_sin_consentimiento_vigente_es_404(client):
    respuesta = client.delete("/v1/consentimientos/cliente-sin-consentimiento")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_tras_revocar_la_consulta_es_404(client):
    _otorgar(client)
    client.delete("/v1/consentimientos/cliente-1")

    respuesta = client.get("/v1/consentimientos/cliente-1")

    assert respuesta.status_code == 404


def test_otorgar_de_nuevo_tras_revocar_da_201_con_id_nuevo(client):
    primero = _otorgar(client).json()
    client.delete("/v1/consentimientos/cliente-1")

    segundo = _otorgar(client)

    assert segundo.status_code == 201
    assert segundo.json()["id"] != primero["id"]


def test_health_metrics_y_correlacion(client):
    salud = client.get("/health/live", headers={"X-Correlation-Id": "c-123"})

    assert salud.json() == {"status": "ok"}
    assert salud.headers["X-Correlation-Id"] == "c-123"
    assert "http_request_duration_seconds" in client.get("/metrics").text
