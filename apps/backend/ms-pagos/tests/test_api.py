from uuid import uuid4

from app.infrastructure.externos import TOKEN_RECHAZO


def _cuerpo(oferta_id=None, token="tok_visa", monto="250000.00"):
    return {
        "solicitud_id": str(uuid4()),
        "oferta_id": str(oferta_id or uuid4()),
        "usuario_id": str(uuid4()),
        "monto": monto,
        "token_medio_pago": token,
    }


def test_cobrar_devuelve_201_y_el_resultado_es_consultable(client):
    cuerpo = _cuerpo()

    respuesta = client.post("/v1/pagos/primas", json=cuerpo)

    assert respuesta.status_code == 201
    pago = respuesta.json()
    assert pago["estado"] == "APROBADO"
    assert pago["idempotency_key"] == f"cobro-prima:{cuerpo['oferta_id']}"
    assert client.get(f"/v1/pagos/{pago['id']}").json() == pago


def test_reintento_devuelve_200_con_el_pago_original(client, pasarela):
    cuerpo = _cuerpo()
    original = client.post("/v1/pagos/primas", json=cuerpo).json()

    reintento = client.post("/v1/pagos/primas", json=cuerpo)

    assert reintento.status_code == 200
    assert reintento.json()["id"] == original["id"]
    assert len(pasarela.movimientos) == 1


def test_cobro_rechazado_se_registra_con_estado_rechazado(client):
    respuesta = client.post("/v1/pagos/primas", json=_cuerpo(token=TOKEN_RECHAZO))

    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "RECHAZADO"


def test_suscripcion_no_aceptada_responde_422(client, suscripciones):
    suscripciones.respuesta = False

    respuesta = client.post("/v1/pagos/primas", json=_cuerpo())

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "suscripcion_no_aceptada"


def test_monto_no_positivo_o_sin_token_responde_422(client):
    assert client.post("/v1/pagos/primas", json=_cuerpo(monto="0")).json()["codigo"] == "monto_no_positivo"
    assert client.post("/v1/pagos/primas", json=_cuerpo(token="")).status_code == 422


def test_consultar_pago_inexistente_responde_404(client):
    respuesta = client.get(f"/v1/pagos/{uuid4()}")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"
