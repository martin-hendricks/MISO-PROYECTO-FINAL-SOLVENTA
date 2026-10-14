from tests.conftest import token


def _auth(client, rol):
    return {"Authorization": f"Bearer {token(client, rol)}"}


def test_cartera_ficha_y_venta(client):
    headers = _auth(client, "asesor")
    assert client.get("/asesor/cartera", headers=headers).status_code == 200
    created = client.post(
        "/asesor/clientes",
        headers=headers,
        json={
            "nombre": "Camila Restrepo",
            "documento": "1012345678",
            "correo": "camila@correo.com",
            "habeasData": True,
        },
    )
    assert "clienteId" not in {
        "nombre": "Camila Restrepo",
        "documento": "1012345678",
        "correo": "camila@correo.com",
        "habeasData": True,
    }
    assert created.status_code == 200
    off = client.post(
        "/asesor/clientes/estado",
        headers=headers,
        json={"clienteId": "CLI-18", "estado": "inactivo"},
    )
    assert off.json()["estado"] == "inactivo"
    sale = client.post(
        "/asesor/cotizaciones",
        headers=headers,
        json={"clienteId": "CLI-18", "ramo": "Protección de dispositivo", "datosRiesgo": {}},
    )
    assert sale.status_code == 200
    assert isinstance(sale.json()["prima"], int)


def test_asesor_no_abre_otras_pantallas(client):
    headers = _auth(client, "asesor")
    assert client.get("/cliente/inicio", headers=headers).status_code == 403
    assert client.get("/operador/avisos", headers=headers).status_code == 403
    assert client.post(
        "/operador/polizas/ciclo",
        headers=headers,
        json={"numero": "POL-1", "verbo": "renovar"},
    ).status_code == 403


def test_cliente_no_abre_pantallas_de_asesor(client):
    headers = _auth(client, "cliente")
    assert client.get("/asesor/cartera", headers=headers).status_code == 403
    assert client.get("/operador/avisos", headers=headers).status_code == 403


def test_listado_de_clientes_trae_canal_y_consentimiento(client):
    clientes = client.get("/asesor/clientes", headers=_auth(client, "asesor")).json()["clientes"]
    assert len({item["clienteId"] for item in clientes}) == len(clientes) == 5
    assert {item["canal"] for item in clientes} == {"web", "android"}
    assert {item["estado"] for item in clientes} == {"activo", "inactivo"}
    revocado = next(item for item in clientes if item["consentimiento"] == "revocado")
    assert revocado["habeasData"] is False


def _venta_a_tercero(**cambios):
    body = {
        "cliente": {"nombre": "Andrés Gómez Molina", "documento": "1020334556"},
        "ramo": "dispositivo",
        "vigenciaMeses": 12,
        "datosRiesgo": {
            "tipo": "telefono",
            "valorAsegurado": 1200000,
            "marca": "Samsung",
            "modelo": "Galaxy A54",
        },
    }
    body.update(cambios)
    return body


def test_venta_a_tercero_desglosa_la_oferta_en_firme(client):
    offer = client.post(
        "/asesor/cotizaciones", headers=_auth(client, "asesor"), json=_venta_a_tercero()
    ).json()
    assert offer["cotizacionId"]
    assert offer["estado"] == "oferta_vigente"
    assert offer["primaNeta"] + offer["gastosExpedicion"] == offer["prima"]
    assert offer["vigenciaMeses"] == 12
    assert offer["moneda"] == "COP"
    assert "locale" not in offer


def test_reconsulta_del_asesor_no_recalcula(client):
    headers = _auth(client, "asesor")
    offer = client.post("/asesor/cotizaciones", headers=headers, json=_venta_a_tercero()).json()
    again = client.get(f"/asesor/cotizaciones/{offer['cotizacionId']}", headers=headers).json()
    for campo in ("cotizacionId", "prima", "primaNeta", "gastosExpedicion", "moneda", "venceEn"):
        assert again[campo] == offer[campo]


def test_venta_sin_cliente_es_422(client):
    response = client.post(
        "/asesor/cotizaciones",
        headers=_auth(client, "asesor"),
        json=_venta_a_tercero(cliente=None),
    )
    assert response.status_code == 422


def test_cliente_no_reconsulta_cotizaciones_del_asesor(client):
    response = client.get("/asesor/cotizaciones/COT-1042", headers=_auth(client, "cliente"))
    assert response.status_code == 403