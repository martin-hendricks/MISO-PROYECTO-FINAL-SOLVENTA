from uuid import uuid4


def _cuerpo(oferta_id=None, token_pago_confirmado=None):
    return {
        "solicitud_id": str(uuid4()),
        "oferta_id": str(oferta_id or uuid4()),
        "usuario_id": str(uuid4()),
        "token_pago_confirmado": str(token_pago_confirmado or uuid4()),
        "coberturas": [{"nombre": "Responsabilidad civil", "suma_asegurada": "50000000.00"}],
    }


def test_emitir_devuelve_201_y_la_poliza_es_consultable_de_inmediato(client):
    respuesta = client.post("/v1/polizas", json=_cuerpo())

    assert respuesta.status_code == 201
    poliza = respuesta.json()
    assert poliza["estado"] == "VIGENTE"
    assert poliza["numero"].startswith("POL-")
    assert poliza["coberturas"][0]["deducible"] == "0"

    consulta = client.get(f"/v1/polizas/{poliza['id']}")
    assert consulta.status_code == 200
    assert consulta.json() == poliza


def test_reintentar_la_emision_devuelve_200_con_la_misma_poliza(client):
    cuerpo = _cuerpo()
    primera = client.post("/v1/polizas", json=cuerpo).json()

    segunda = client.post("/v1/polizas", json=cuerpo)

    assert segunda.status_code == 200
    assert segunda.json()["numero"] == primera["numero"]


def test_suscripcion_no_aceptada_responde_422(client, suscripciones):
    suscripciones.respuesta = False

    respuesta = client.post("/v1/polizas", json=_cuerpo())

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "suscripcion_no_aceptada"


def test_cobro_no_exitoso_responde_422(client, cobros):
    cobros.respuesta = False

    respuesta = client.post("/v1/polizas", json=_cuerpo())

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "cobro_no_exitoso"


def test_sin_coberturas_o_con_token_de_pago_invalido_responde_422(client):
    sin_coberturas = {**_cuerpo(), "coberturas": []}

    assert client.post("/v1/polizas", json=sin_coberturas).status_code == 422
    assert client.post("/v1/polizas", json=_cuerpo(token_pago_confirmado="PAGO-1")).status_code == 422


def test_consultar_poliza_inexistente_responde_404(client):
    respuesta = client.get(f"/v1/polizas/{uuid4()}")

    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"
