from uuid import uuid4


def _evaluar(client, solicitud_id=None, score="0.40"):
    return client.post(
        "/v1/suscripciones",
        json={"solicitud_id": str(solicitud_id or uuid4()), "perfil_id": str(uuid4()), "score": score},
    )


def test_riesgo_dentro_del_apetito(client):
    """Escenario: Riesgo dentro del apetito."""
    solicitud = uuid4()

    respuesta = _evaluar(client, solicitud, score="0.40")

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["decision"] == "ACEPTADA"
    assert cuerpo["motivo"] == "Riesgo dentro del apetito"
    assert cuerpo["regla"] == "Score de riesgo hasta 0.7"
    assert cuerpo["evaluada_en"]
    # El flujo continúa: cobro (HU-15) y emisión (HU-16) consultan esta decisión.
    consulta = client.get(f"/v1/suscripciones/{solicitud}")
    assert consulta.status_code == 200
    assert consulta.json()["decision"] == "ACEPTADA"


def test_riesgo_fuera_del_apetito(client, almacen):
    """Escenario: Riesgo fuera del apetito."""
    solicitud = uuid4()

    respuesta = _evaluar(client, solicitud, score="0.95")

    assert respuesta.status_code == 201
    assert respuesta.json()["decision"] == "RECHAZADA"
    assert respuesta.json()["motivo"] == "Riesgo fuera del apetito"
    # El motivo persistido es el que leen los canales; cobro y emisión ven el rechazo.
    consulta = client.get(f"/v1/suscripciones/{solicitud}").json()
    assert consulta["decision"] == "RECHAZADA"
    assert consulta["motivo"] == "Riesgo fuera del apetito"
    assert almacen.eventos[0].payload["decision"] == "RECHAZADA"


def test_reintento_responde_200_con_la_misma_decision(client):
    solicitud = uuid4()
    primero = _evaluar(client, solicitud, score="0.95")

    reintento = _evaluar(client, solicitud, score="0.10")

    assert reintento.status_code == 200
    assert reintento.json()["suscripcion_id"] == primero.json()["suscripcion_id"]
    assert reintento.json()["decision"] == "RECHAZADA"


def test_score_negativo_es_422(client):
    assert _evaluar(client, score="-1").status_code == 422


def test_solicitud_sin_decision_es_404_con_codigo(client):
    respuesta = client.get(f"/v1/suscripciones/{uuid4()}")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_sin_regla_vigente_es_503(client, almacen):
    almacen.regla = None

    respuesta = _evaluar(client)

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "regla_no_configurada"


def test_health_ready_sin_base_de_datos_devuelve_503(client):
    # El cliente de pruebas crea la app real (lifespan real -> motor SQLAlchemy real)
    # pero sin un Postgres escuchando en DATABASE_URL: el ping debe fallar controladamente.
    respuesta = client.get("/health/ready")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable"}
