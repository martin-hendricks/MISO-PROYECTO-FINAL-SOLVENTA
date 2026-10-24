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


def _emitir(client) -> dict:
    return client.post("/v1/polizas", json=_cuerpo()).json()


def test_renovar_extiende_la_vigencia_y_responde_200(client):
    poliza = _emitir(client)

    respuesta = client.post(
        f"/v1/polizas/{poliza['id']}/renovacion", json={"nueva_fin_vigencia": "2029-01-01"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["fin_vigencia"] == "2029-01-01"
    assert respuesta.json()["estado"] == "VIGENTE"


def test_renovar_poliza_inexistente_responde_404(client):
    respuesta = client.post(f"/v1/polizas/{uuid4()}/renovacion", json={"nueva_fin_vigencia": "2029-01-01"})

    assert respuesta.status_code == 404


def test_modificar_coberturas_responde_200_con_las_nuevas_coberturas(client):
    poliza = _emitir(client)

    respuesta = client.post(
        f"/v1/polizas/{poliza['id']}/coberturas",
        json={"coberturas": [{"nombre": "Robo", "suma_asegurada": "1000.00"}]},
    )

    assert respuesta.status_code == 200
    assert [c["nombre"] for c in respuesta.json()["coberturas"]] == ["Robo"]


def test_modificar_coberturas_vacias_responde_422(client):
    poliza = _emitir(client)

    respuesta = client.post(f"/v1/polizas/{poliza['id']}/coberturas", json={"coberturas": []})

    assert respuesta.status_code == 422


def test_cancelar_responde_200_y_queda_cancelada(client):
    poliza = _emitir(client)

    respuesta = client.post(f"/v1/polizas/{poliza['id']}/cancelacion", json={"motivo": "El cliente lo pidió"})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "CANCELADA"
    assert cuerpo["motivo_cancelacion"] == "El cliente lo pidió"


def test_cancelar_sin_motivo_responde_422(client):
    poliza = _emitir(client)

    respuesta = client.post(f"/v1/polizas/{poliza['id']}/cancelacion", json={"motivo": ""})

    assert respuesta.status_code == 422


def test_cancelar_dos_veces_responde_409(client):
    poliza = _emitir(client)
    client.post(f"/v1/polizas/{poliza['id']}/cancelacion", json={"motivo": "El cliente lo pidió"})

    respuesta = client.post(f"/v1/polizas/{poliza['id']}/cancelacion", json={"motivo": "Otro motivo"})

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "transicion_invalida"


def test_renovar_poliza_cancelada_responde_409(client):
    poliza = _emitir(client)
    client.post(f"/v1/polizas/{poliza['id']}/cancelacion", json={"motivo": "El cliente lo pidió"})

    respuesta = client.post(
        f"/v1/polizas/{poliza['id']}/renovacion", json={"nueva_fin_vigencia": "2029-01-01"}
    )

    assert respuesta.status_code == 409
