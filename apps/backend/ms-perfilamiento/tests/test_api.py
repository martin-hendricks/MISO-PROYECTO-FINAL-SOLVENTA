CLAVE = {"Idempotency-Key": "clave-0001"}


def test_otorgar_consentimiento_201_y_reintento_200(client):
    primero = client.post("/v1/consentimientos", json={"cliente_id": "cliente-1"})
    reintento = client.post("/v1/consentimientos", json={"cliente_id": "cliente-1"})

    assert primero.status_code == 201
    assert primero.json()["vigente"] is True
    assert reintento.status_code == 200
    assert reintento.json()["id"] == primero.json()["id"]


def test_consultar_consentimiento_inexistente_es_404(client):
    respuesta = client.get("/v1/consentimientos/cliente-fantasma")
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_revocar_consentimiento_impide_futura_consulta(client):
    client.post("/v1/consentimientos", json={"cliente_id": "cliente-1"})

    revocado = client.delete("/v1/consentimientos/cliente-1")
    assert revocado.status_code == 200
    assert revocado.json()["vigente"] is False

    assert client.get("/v1/consentimientos/cliente-1").status_code == 404


def test_revocar_sin_consentimiento_previo_es_404(client):
    respuesta = client.delete("/v1/consentimientos/cliente-sin-consentimiento")
    assert respuesta.status_code == 404


def test_solicitar_oferta_sin_consentimiento_es_403(client):
    respuesta = client.post(
        "/v1/ofertas-hipotecario", json={"cliente_id": "cliente-sin-consentimiento"}, headers=CLAVE
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "consentimiento_no_otorgado"


def test_solicitar_oferta_con_consentimiento_devuelve_precio_y_factores(client):
    client.post("/v1/consentimientos", json={"cliente_id": "cliente-1"})

    respuesta = client.post("/v1/ofertas-hipotecario", json={"cliente_id": "cliente-1"}, headers=CLAVE)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["precio"]
    assert cuerpo["degradado"] is False
    assert len(cuerpo["factores"]) == 4
    assert all({"factor", "impacto", "peso"} <= f.keys() for f in cuerpo["factores"])
    assert len(cuerpo["snapshot_atributos"]) == 4


def test_solicitar_oferta_reintento_misma_clave_devuelve_200_mismo_id(client):
    client.post("/v1/consentimientos", json={"cliente_id": "cliente-1"})

    primero = client.post("/v1/ofertas-hipotecario", json={"cliente_id": "cliente-1"}, headers=CLAVE)
    reintento = client.post("/v1/ofertas-hipotecario", json={"cliente_id": "cliente-1"}, headers=CLAVE)

    assert primero.status_code == 201
    assert reintento.status_code == 200
    assert reintento.json()["id"] == primero.json()["id"]


def test_solicitar_oferta_sin_idempotency_key_es_422(client):
    respuesta = client.post("/v1/ofertas-hipotecario", json={"cliente_id": "cliente-1"})
    assert respuesta.status_code == 422


def test_health_metrics_y_correlacion(client):
    salud = client.get("/health", headers={"X-Correlation-Id": "c-123"})

    assert salud.json() == {"status": "ok"}
    assert salud.headers["X-Correlation-Id"] == "c-123"
    assert "http_request_duration_seconds" in client.get("/metrics").text
