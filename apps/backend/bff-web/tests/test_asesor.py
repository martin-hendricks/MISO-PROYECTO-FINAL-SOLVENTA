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
