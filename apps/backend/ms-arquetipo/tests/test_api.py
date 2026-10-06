from uuid import uuid4

CLAVE = {"Idempotency-Key": "clave-0001"}


def _registrar(client, clave="clave-0001", **cuerpo):
    return client.post(
        "/v1/ejemplos",
        json={"referencia": "REF-1", "monto": "100.00", **cuerpo},
        headers={"Idempotency-Key": clave},
    )


def test_registrar_201_y_reintento_200_mismo_id(client):
    primero = _registrar(client)
    reintento = _registrar(client)

    assert primero.status_code == 201
    assert reintento.status_code == 200
    assert reintento.json()["id"] == primero.json()["id"]


def test_registrar_sin_idempotency_key_es_422(client):
    respuesta = client.post("/v1/ejemplos", json={"referencia": "R", "monto": "1"})
    assert respuesta.status_code == 422


def test_regla_de_negocio_se_traduce_a_422_con_codigo(client):
    respuesta = _registrar(client, monto="0")
    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "monto_no_positivo"


def test_consultar_listar_e_indicadores(client):
    creado = _registrar(client).json()

    assert client.get(f"/v1/ejemplos/{creado['id']}").json()["referencia"] == "REF-1"
    assert [e["id"] for e in client.get("/v1/ejemplos?limite=5").json()] == [creado["id"]]
    assert client.get("/v1/ejemplos/indicadores").json() == {"total": 1, "monto_total": "100.00"}


def test_inexistente_es_404(client):
    respuesta = client.get(f"/v1/ejemplos/{uuid4()}")
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_aprobar_dos_veces_es_409(client):
    creado = _registrar(client).json()

    assert client.post(f"/v1/ejemplos/{creado['id']}/aprobacion").status_code == 200
    assert client.post(f"/v1/ejemplos/{creado['id']}/aprobacion").status_code == 409


def test_health_metrics_y_correlacion(client):
    salud = client.get("/health", headers={"X-Correlation-Id": "c-123"})

    assert salud.json() == {"status": "ok"}
    assert salud.headers["X-Correlation-Id"] == "c-123"
    assert "http_request_duration_seconds" in client.get("/metrics").text
