from tests.conftest import token


def _auth(client):
    return {"Authorization": f"Bearer {token(client, 'operador')}"}


def test_cola_sin_asistencia(client):
    body = client.get("/operador/avisos", headers=_auth(client)).json()
    assert body["avisos"]
    assert all("asistenciaId" not in item for item in body["avisos"])


def test_rechazo_sin_motivo_es_400(client):
    response = client.post(
        "/operador/avisos/decision",
        headers=_auth(client),
        json={"siniestroId": "SIN-441", "decision": "rechazar"},
    )
    assert response.status_code == 400


def test_cancelar_sin_motivo_es_400_y_con_motivo_cambia_estado(client):
    headers = _auth(client)
    missing = client.post(
        "/operador/polizas/ciclo",
        headers=headers,
        json={"numero": "POL-88219-CO", "verbo": "cancelar"},
    )
    assert missing.status_code == 400
    done = client.post(
        "/operador/polizas/ciclo",
        headers=headers,
        json={"numero": "POL-88219-CO", "verbo": "cancelar", "motivo": "El cliente lo pidió"},
    )
    assert done.status_code == 200
    assert done.json()["estado"] == "cancelada"


def test_estado_de_asistencia(client):
    body = client.get("/operador/asistencias/AS-18", headers=_auth(client)).json()
    assert body["asistenciaId"] == "AS-18"
    assert body["estado"] == "registrada"


def test_operador_no_abre_cartera(client):
    assert client.get("/asesor/cartera", headers=_auth(client)).status_code == 403
