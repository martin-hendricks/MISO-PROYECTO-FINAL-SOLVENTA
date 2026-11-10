import httpx

from tests.conftest import token

SID = "7b0c0000-0000-4000-8000-000000000001"
PAGO = {
    "siniestro_id": SID,
    "numero": "SIN-1002",
    "tipo": "parametrico",
    "ramo": "proteccion-dispositivo",
    "poliza_numero": "POL-11002-CO",
    "descripcion": "retraso de vuelo",
    "monto": "180000.00",
    "comprobante": "CMP-0A77B2C4F1",
    "clave": "evt-vuelo",
    "pagado_en": "2026-07-02T09:05:00+00:00",
}


def auth(client, rol="cliente"):
    return {"Authorization": f"Bearer {token(client, rol)}"}


def test_billetera_traduce_el_pago_parametrico(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/pagos-recibidos")] = lambda _: httpx.Response(
        200, json={"moneda": "COP", "total": "180000.00", "pagos": [PAGO]}
    )
    cuerpo = client.get("/v1/cliente/billetera", headers=auth(client)).json()
    assert cuerpo["totalRecibido"] == 180000
    movimiento = cuerpo["movimientos"][0]
    assert movimiento["tipo"] == "pago_automatico"
    assert movimiento["ramo"] == "Protección de dispositivo"
    assert movimiento["siniestroId"] == "SIN-1002"
    assert movimiento["id"] == SID
    assert nucleo_siniestros.peticiones[-1].url.path == "/v1/pagos-recibidos"
    assert not any(p.url.path == "/v1/siniestros" for p in nucleo_siniestros.peticiones)


def test_detalle_ajeno_es_404(client, nucleo_siniestros):
    respuesta = client.get(f"/v1/cliente/billetera/{SID}", headers=auth(client))
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_caida_del_nucleo_es_503(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/pagos-recibidos")] = lambda _: httpx.Response(503, json={})
    respuesta = client.get("/v1/cliente/billetera", headers=auth(client))
    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "servicio_no_disponible"


def test_sin_bearer_no_llama_al_nucleo(client, nucleo_siniestros):
    assert client.get("/v1/cliente/billetera").status_code == 401
    assert nucleo_siniestros.peticiones == []


def test_rol_distinto_de_cliente_es_403(client, nucleo_siniestros):
    assert client.get("/v1/cliente/billetera", headers=auth(client, "operador")).status_code == 403
    assert nucleo_siniestros.peticiones == []


def test_id_que_no_es_uuid_es_422(client):
    assert client.get("/v1/cliente/billetera/no-es-uuid", headers=auth(client)).status_code == 422
