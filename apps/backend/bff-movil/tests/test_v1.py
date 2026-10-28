import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.clients.bff_web import ClienteBffWeb
from app.main import app
from tests.conftest import customer_token, desk_token

AVISO = {
    "poliza": "POL-88219-CO",
    "fechaHecho": "2026-03-12",
    "geo": None,
    "adjuntos": [],
}
ALTA = {
    "nombre": "Camila",
    "apellidos": "Restrepo",
    "documento": "1012345678",
    "correo": "camila@correo.com",
    "habeasData": True,
    "pruebaDeVida": "ok",
}
CLAVES_POLIZA = {"numero", "ramo", "resumen", "estado", "venceEn"}


class DobleBffWeb:
    def __init__(self, cuerpo: dict | None = None) -> None:
        self.llamadas: list[dict] = []
        self.cuerpo = {} if cuerpo is None else cuerpo

    def enviar(self, metodo: str, ruta: str, *, json=None, autorizacion=None) -> dict:
        self.llamadas.append(
            {"metodo": metodo, "ruta": ruta, "json": json, "autorizacion": autorizacion}
        )
        return self.cuerpo


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def doble():
    anterior = app.state.bff_web
    doble_web = DobleBffWeb()
    app.state.bff_web = doble_web
    yield doble_web
    app.state.bff_web = anterior


def _auth(client: TestClient) -> dict:
    return {"Authorization": f"Bearer {customer_token(client)}"}


def test_v0_no_llama_a_bff_web(client, doble):
    headers = _auth(client)
    billetera = client.get("/cliente/polizas", headers=headers)
    aviso = client.post("/cliente/siniestros", headers=headers, json=AVISO)
    assert billetera.status_code == 200
    assert billetera.json()["polizas"][0]["numero"] == "POL-88219-CO"
    assert aviso.status_code == 200
    assert aviso.json()["siniestroId"] == "SIN-441"
    assert doble.llamadas == []


def test_billetera_v1_descarta_campos_web(client, doble):
    doble.cuerpo = {
        "polizas": [
            {
                "numero": "POL-1",
                "ramo": "Vida",
                "resumen": "Robo",
                "estado": "vigente",
                "venceEn": "2027-01-01",
                "interno": "web",
            }
        ]
    }
    body = client.get("/v1/cliente/polizas", headers=_auth(client)).json()
    assert set(body["polizas"][0]) == CLAVES_POLIZA
    assert body["polizas"][0]["numero"] == "POL-1"


def test_billetera_v1_incompleta_es_502(client, doble):
    doble.cuerpo = {"polizas": [{"numero": "POL-1"}]}
    response = client.get("/v1/cliente/polizas", headers=_auth(client))
    assert response.status_code == 502
    assert "POL-88219-CO" not in response.text


def test_ingreso_v1_reenvia_sin_rol_y_devuelve_el_par(client, doble):
    doble.cuerpo = {
        "accessToken": "access-web",
        "refreshToken": "refresh-web",
        "expiraEn": 90,
        "rol": "asesor",
    }
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    )
    assert response.status_code == 200
    assert response.json() == doble.cuerpo
    assert doble.llamadas[0]["metodo"] == "POST"
    assert doble.llamadas[0]["ruta"] == "/v1/sesion/ingreso"
    assert doble.llamadas[0]["json"] == {
        "correo": "camila@correo.com",
        "contrasena": "secreto",
    }


def test_refresh_v1_devuelve_el_par(client, doble):
    doble.cuerpo = {"accessToken": "a2", "refreshToken": "r2", "expiraEn": 90}
    response = client.post("/v1/sesion/refresh", json={"refreshToken": "r1"})
    assert response.json() == doble.cuerpo
    assert doble.llamadas[0]["ruta"] == "/v1/sesion/refresh"
    assert doble.llamadas[0]["json"] == {"refreshToken": "r1"}


def test_cotizacion_v1_no_envia_cliente_id_ni_rol(client, doble):
    doble.cuerpo = {
        "cotizacionId": "COT-9",
        "ramo": "Vida",
        "estado": "oferta_vigente",
        "prima": 10,
        "moneda": "COP",
        "venceEn": "2027-01-01",
        "canal": "web",
    }
    response = client.post(
        "/v1/cliente/cotizaciones",
        headers=_auth(client),
        json={"ramo": "Vida", "datosRiesgo": {"valor": 1}, "rol": "operador"},
    )
    assert response.status_code == 200
    assert "canal" not in response.json()
    assert doble.llamadas[0]["json"] == {"ramo": "Vida", "datosRiesgo": {"valor": 1}}
    assert doble.llamadas[0]["autorizacion"].startswith("Bearer ")


def test_aceptar_emitida_y_rechazada(client, doble):
    headers = _auth(client)
    doble.cuerpo = {
        "resultado": "EMITIDA",
        "poliza": {
            "numero": "POL-9",
            "ramo": "Vida",
            "estado": "vigente",
            "venceEn": "2027-01-01",
            "coberturas": [],
        },
    }
    emitida = client.post(
        "/v1/cliente/polizas",
        headers=headers,
        json={"cotizacionId": "COT-9"},
    )
    assert emitida.json() == {
        "numero": "POL-9",
        "ramo": "Vida",
        "estado": "vigente",
        "venceEn": "2027-01-01",
    }
    assert doble.llamadas[0]["json"] == {"cotizacionId": "COT-9"}
    doble.cuerpo = {"resultado": "RECHAZADA", "motivo": "fuera de rango"}
    rechazada = client.post(
        "/v1/cliente/polizas",
        headers=headers,
        json={"cotizacionId": "COT-RECHAZADA"},
    )
    assert rechazada.json() == {"estado": "rechazada", "motivo": "fuera de rango"}


def test_ruta_mapeada_sin_url_es_503(client):
    anterior = app.state.bff_web
    app.state.bff_web = ClienteBffWeb("")
    try:
        response = client.get("/v1/cliente/polizas", headers=_auth(client))
    finally:
        app.state.bff_web = anterior
    assert response.status_code == 503
    assert response.json()["detail"] == "BFF_WEB_BASE_URL no configurado"


def test_sin_bearer_v1_es_401_y_no_llama(client, doble):
    response = client.get("/v1/cliente/polizas")
    assert response.status_code == 401
    assert response.json()["detail"] == "Token requerido"
    assert doble.llamadas == []


def test_rol_no_cliente_v1_es_403(client, doble):
    for rol in ("asesor", "operador"):
        headers = {"Authorization": f"Bearer {desk_token(rol)}"}
        response = client.get("/v1/cliente/polizas", headers=headers)
        assert response.status_code == 403
        assert response.json()["detail"] == "Rol no autorizado"
    assert doble.llamadas == []


def test_rutas_sin_mapa_no_llaman_y_el_aviso_es_estable(client, doble):
    headers = _auth(client)
    alta = client.post("/v1/registro", json=ALTA)
    assert alta.status_code == 200
    assert alta.json()["pruebaDeVida"] == "ok"
    consentimiento = client.post(
        "/v1/registro/consentimiento",
        json={"habeasData": False},
    )
    assert consentimiento.json() == {"habeasData": False}
    primero = client.post("/v1/cliente/siniestros", headers=headers, json=AVISO)
    segundo = client.post("/v1/cliente/siniestros", headers=headers, json=AVISO)
    assert primero.json() == {"siniestroId": "SIN-441", "estado": "recibido"}
    assert segundo.json()["siniestroId"] == "SIN-441"
    assert client.get("/v1/cliente/siniestros", headers=headers).status_code == 200
    assert client.get("/v1/cliente/avisos", headers=headers).status_code == 200
    token = client.post(
        "/v1/cliente/avisos/token",
        headers=headers,
        json={"token": "fcm", "plataforma": "android"},
    )
    assert token.status_code == 200
    assert client.get("/v1/cliente/avisos/push", headers=headers).status_code == 200
    assert client.get("/v1/cliente/prestadores", headers=headers).status_code == 200
    asistencia = client.post(
        "/v1/cliente/asistencias",
        headers=headers,
        json={
            "prestadorId": "PR-1",
            "geo": {"lat": 4.65, "lng": -74.08, "precisionM": 12},
            "poliza": "POL-88219-CO",
        },
    )
    assert asistencia.json()["estado"] == "registrada"
    assert doble.llamadas == []


def test_prueba_de_vida_v1_solo_ok_o_no(client, doble):
    response = client.post("/v1/registro", json={**ALTA, "pruebaDeVida": "maybe"})
    assert response.status_code == 400
    assert doble.llamadas == []


def test_salida_v1_reenvia_el_bearer(client, doble):
    doble.cuerpo = {"estado": "aceptada"}
    headers = _auth(client)
    response = client.post("/v1/sesion/salida", headers=headers)
    assert response.status_code == 200
    assert doble.llamadas[0]["ruta"] == "/v1/sesion/salida"
    assert doble.llamadas[0]["autorizacion"] == headers["Authorization"]


def test_rutas_equivocadas_del_cliente_no_existen(client):
    headers = _auth(client)
    assert client.post("/registro/revocacion", json={"habeasData": False}).status_code == 404
    assert client.post("/cliente/push", headers=headers).status_code == 404
    assert client.post("/cliente/polizas/POL-1/ciclo", headers=headers).status_code == 404
    assert client.post("/v1/operador/polizas/ciclo", headers=headers).status_code == 404


def test_cliente_real_sin_url_no_abre_socket():
    with pytest.raises(HTTPException) as exc:
        ClienteBffWeb("").enviar("GET", "/v1/cliente/polizas")
    assert exc.value.status_code == 503
    assert exc.value.detail == "BFF_WEB_BASE_URL no configurado"
