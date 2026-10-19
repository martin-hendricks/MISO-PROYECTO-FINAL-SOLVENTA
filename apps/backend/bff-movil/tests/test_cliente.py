from tests.conftest import customer_token


def _auth(client):
    return {"Authorization": f"Bearer {customer_token(client)}"}


def test_cotizacion_poliza_y_pago(client):
    headers = _auth(client)
    offer = client.post(
        "/cliente/cotizaciones",
        headers=headers,
        json={"ramo": "Protección de dispositivo", "datosRiesgo": {"valorDispositivo": 2400000}},
    ).json()
    assert isinstance(offer["prima"], int) and offer["moneda"] == "COP"
    again = client.get(f"/cliente/cotizaciones/{offer['cotizacionId']}", headers=headers)
    assert again.json()["cotizacionId"] == offer["cotizacionId"]
    refused = client.post(
        "/cliente/polizas",
        headers=headers,
        json={"cotizacionId": "COT-RECHAZADA"},
    ).json()
    assert refused["motivo"] == "Valor del equipo fuera de rango"
    detail = client.get("/cliente/polizas/POL-88219-CO", headers=headers).json()
    assert detail["queHacer"]
    payment = client.get("/cliente/pagos-automaticos", headers=headers).json()
    assert isinstance(payment["monto"], int) and "locale" not in payment


def test_aviso_sin_geo(client):
    response = client.post(
        "/cliente/siniestros",
        headers=_auth(client),
        json={
            "poliza": "POL-88219-CO",
            "fechaHecho": "2026-03-12",
            "geo": None,
            "adjuntos": [{"tipo": "foto", "nombre": "dano.jpg"}],
        },
    )
    assert response.status_code == 200
    assert response.json()["estado"] == "recibido"


def test_hipoteca_avisos_inicio_push_y_asistencia(client):
    headers = _auth(client)
    degraded = client.post(
        "/cliente/oferta-hipotecaria",
        headers=headers,
        json={"credito": {"valor": 1, "plazoMeses": 12}, "consentimientoPerfil": False},
    ).json()
    assert degraded["degradada"] is True and degraded["prima"] == 50000
    assert client.get("/cliente/avisos", headers=headers).json()["avisos"]
    assert client.get("/cliente/inicio", headers=headers).json()["hipotecario"] is None
    token = client.post(
        "/cliente/avisos/token",
        headers=headers,
        json={"token": "fcm-stub", "plataforma": "android"},
    )
    assert token.status_code == 200
    push = client.get("/cliente/avisos/push", headers=headers).json()
    assert push["destino"] == "aviso-vencimiento"
    providers = client.get("/cliente/prestadores", headers=headers).json()
    assert providers["prestadores"][0]["id"] == "PR-1"
    assistance = client.post(
        "/cliente/asistencias",
        headers=headers,
        json={
            "prestadorId": "PR-1",
            "geo": {"lat": 4.65, "lng": -74.08, "precisionM": 12},
            "poliza": "POL-88219-CO",
        },
    ).json()
    assert assistance == {"asistenciaId": "AS-18", "estado": "registrada"}
