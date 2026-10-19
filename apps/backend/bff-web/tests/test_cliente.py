from tests.conftest import token


def _auth(client, rol="cliente"):
    return {"Authorization": f"Bearer {token(client, rol)}"}


def test_cotizacion_y_reconsulta(client):
    headers = _auth(client)
    created = client.post(
        "/cliente/cotizaciones",
        headers=headers,
        json={"ramo": "Protección de dispositivo", "datosRiesgo": {"valorDispositivo": 2400000}},
    )
    assert created.status_code == 200
    offer = created.json()
    assert isinstance(offer["prima"], int)
    assert offer["moneda"] == "COP"
    assert "locale" not in offer
    again = client.get(f"/cliente/cotizaciones/{offer['cotizacionId']}", headers=headers)
    assert again.json() == offer


def test_cliente_id_en_cotizacion_de_cliente_es_400(client):
    response = client.post(
        "/cliente/cotizaciones",
        headers=_auth(client),
        json={"ramo": "x", "datosRiesgo": {}, "clienteId": "CLI-18"},
    )
    assert response.status_code == 400


def test_emision_rechazada(client):
    response = client.post(
        "/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": "COT-RECHAZADA"},
    )
    assert response.json() == {
        "estado": "rechazada",
        "motivo": "Valor del equipo fuera de rango",
    }


def test_billetera_y_detalle(client):
    headers = _auth(client)
    wallet = client.get("/cliente/polizas", headers=headers).json()
    assert "polizas" in wallet
    detail = client.get("/cliente/polizas/POL-88219-CO", headers=headers).json()
    assert detail["queHacer"]


def test_pago_automatico_es_numero(client):
    body = client.get("/cliente/pagos-automaticos", headers=_auth(client)).json()
    assert isinstance(body["monto"], int)
    assert body["moneda"] == "COP"
    assert "locale" not in body


def test_hipoteca_degradada_no_espera(client):
    headers = _auth(client)
    ready = client.post(
        "/cliente/oferta-hipotecaria",
        headers=headers,
        json={"credito": {"valor": 180000000, "plazoMeses": 180}, "consentimientoPerfil": True},
    ).json()
    degraded = client.post(
        "/cliente/oferta-hipotecaria",
        headers=headers,
        json={"credito": {"valor": 180000000, "plazoMeses": 180}, "consentimientoPerfil": False},
    ).json()
    assert ready["prima"] == 64000 and ready["degradada"] is False
    assert degraded["prima"] == 50000 and degraded["degradada"] is True
    assert degraded["moneda"] == "COP"


def test_inicio(client):
    body = client.get("/cliente/inicio", headers=_auth(client)).json()
    assert body["hipotecario"] is None


def test_sin_token_es_401(client):
    assert client.get("/cliente/inicio").status_code == 401
