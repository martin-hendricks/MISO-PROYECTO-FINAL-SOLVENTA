import httpx

from tests.conftest import token

POLIZA_ID = "77777777-7777-7777-7777-777777777777"

POLIZA_VIGENTE = {
    "id": POLIZA_ID,
    "numero": "POL-88219-CO",
    "oferta_id": "22222222-2222-2222-2222-222222222222",
    "usuario_id": "66666666-6666-6666-6666-666666666666",
    "inicio_vigencia": "2026-10-01",
    "fin_vigencia": "2027-10-01",
    "estado": "VIGENTE",
    "coberturas": [{"nombre": "RC", "suma_asegurada": "1000.00", "deducible": "0"}],
}

POLIZA_CANCELADA = {**POLIZA_VIGENTE, "estado": "CANCELADA", "motivo_cancelacion": "El cliente lo pidió"}


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


def test_cancelar_sin_motivo_es_400(client):
    response = client.post(
        "/operador/polizas/ciclo",
        headers=_auth(client),
        json={"numero": "POL-88219-CO", "polizaId": POLIZA_ID, "verbo": "cancelar"},
    )
    assert response.status_code == 400


def test_ciclo_con_verbo_no_permitido_es_400(client):
    response = client.post(
        "/operador/polizas/ciclo",
        headers=_auth(client),
        json={"numero": "POL-88219-CO", "polizaId": POLIZA_ID, "verbo": "eliminar"},
    )
    assert response.status_code == 400


def test_ciclo_sin_poliza_id_responde_501(client):
    response = client.post(
        "/operador/polizas/ciclo",
        headers=_auth(client),
        json={"numero": "POL-88219-CO", "verbo": "cancelar", "motivo": "El cliente lo pidió"},
    )
    assert response.status_code == 501


def test_cancelar_con_poliza_id_y_motivo_cambia_estado(client, nucleo_polizas):
    nucleo_polizas.respuestas[("POST", f"/v1/polizas/{POLIZA_ID}/cancelacion")] = lambda _: httpx.Response(
        200, json=POLIZA_CANCELADA
    )

    response = client.post(
        "/operador/polizas/ciclo",
        headers=_auth(client),
        json={"numero": "POL-88219-CO", "polizaId": POLIZA_ID, "verbo": "cancelar", "motivo": "El cliente lo pidió"},
    )

    assert response.status_code == 200
    assert response.json()["estado"] == "cancelada"
    peticion = nucleo_polizas.peticiones[-1]
    import json as _json

    assert _json.loads(peticion.read())["motivo"] == "El cliente lo pidió"


def test_renovar_con_poliza_id_cambia_vigencia(client, nucleo_polizas):
    nucleo_polizas.respuestas[("POST", f"/v1/polizas/{POLIZA_ID}/renovacion")] = lambda _: httpx.Response(
        200, json=POLIZA_VIGENTE
    )

    response = client.post(
        "/operador/polizas/ciclo",
        headers=_auth(client),
        json={"numero": "POL-88219-CO", "polizaId": POLIZA_ID, "verbo": "renovar"},
    )

    assert response.status_code == 200
    assert response.json()["estado"] == "vigente"


def test_modificar_sin_coberturas_es_400(client):
    response = client.post(
        "/operador/polizas/ciclo",
        headers=_auth(client),
        json={"numero": "POL-88219-CO", "polizaId": POLIZA_ID, "verbo": "modificar"},
    )
    assert response.status_code == 400


def test_modificar_con_coberturas_reemplaza_coberturas(client, nucleo_polizas):
    nucleo_polizas.respuestas[("POST", f"/v1/polizas/{POLIZA_ID}/coberturas")] = lambda _: httpx.Response(
        200, json=POLIZA_VIGENTE
    )

    response = client.post(
        "/operador/polizas/ciclo",
        headers=_auth(client),
        json={
            "numero": "POL-88219-CO",
            "polizaId": POLIZA_ID,
            "verbo": "modificar",
            "coberturas": [{"nombre": "RC", "suma_asegurada": "1000.00"}],
        },
    )

    assert response.status_code == 200
    assert response.json()["estado"] == "vigente"


def test_ciclo_con_transicion_invalida_del_nucleo_se_propaga_409(client, nucleo_polizas):
    nucleo_polizas.respuestas[("POST", f"/v1/polizas/{POLIZA_ID}/cancelacion")] = lambda _: httpx.Response(
        409, json={"codigo": "transicion_invalida", "mensaje": "No se puede pasar de 'CANCELADA' a 'CANCELADA'"}
    )

    response = client.post(
        "/operador/polizas/ciclo",
        headers=_auth(client),
        json={"numero": "POL-88219-CO", "polizaId": POLIZA_ID, "verbo": "cancelar", "motivo": "Otro motivo"},
    )

    assert response.status_code == 409
    assert response.json()["codigo"] == "transicion_invalida"


def test_estado_de_asistencia(client):
    body = client.get("/operador/asistencias/AS-18", headers=_auth(client)).json()
    assert body["asistenciaId"] == "AS-18"
    assert body["estado"] == "registrada"


def test_operador_no_abre_cartera(client):
    assert client.get("/asesor/cartera", headers=_auth(client)).status_code == 403
