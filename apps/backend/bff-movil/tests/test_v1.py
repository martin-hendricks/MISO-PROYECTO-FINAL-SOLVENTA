import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.clients.nucleo import DETALLE_INCOMPLETA, ClienteNucleo
from app.dependencies import secret
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
COTIZACION = {
    "cotizacion_id": "COT-9",
    "estado": "oferta_vigente",
    "producto": "vida",
    "prima": "10.00",
    "moneda": "COP",
    "vence_en": "2027-01-01",
}
POLIZA = {
    "numero": "POL-9",
    "estado": "vigente",
    "fin_vigencia": "2027-01-01",
    "oferta_id": "oferta-1",
    "coberturas": [{"nombre": "Robo"}],
}
ACEPTADA = {
    "decision": "ACEPTADA",
    "oferta_id": "oferta-1",
    "cotizacion_id": "COT-9",
    "prima": "10.00",
    "estado": "aceptada",
}


class DobleNucleo:
    def __init__(self) -> None:
        self.llamadas: list[dict] = []
        self.respuestas: dict = {}

    def _llamar(self, nombre: str, **kwargs):
        self.llamadas.append({"metodo": nombre, **kwargs})
        valor = self.respuestas.get(nombre, {})
        if isinstance(valor, Exception):
            raise valor
        return valor

    def autenticar(self, *, correo, contrasena):
        return self._llamar("autenticar", correo=correo, contrasena=contrasena)

    def cotizar(self, **kwargs):
        return self._llamar("cotizar", **kwargs)

    def reconsultar(self, cotizacion_id):
        return self._llamar("reconsultar", cotizacion_id=cotizacion_id)

    def reconsultar_por_oferta(self, oferta_id):
        return self._llamar("reconsultar_por_oferta", oferta_id=oferta_id)

    def aceptar_oferta(self, **kwargs):
        return self._llamar("aceptar_oferta", **kwargs)

    def cobrar_prima(self, **kwargs):
        return self._llamar("cobrar_prima", **kwargs)

    def emitir(self, **kwargs):
        return self._llamar("emitir", **kwargs)

    def listar_polizas(self, **kwargs):
        return self._llamar("listar_polizas", **kwargs)

    def obtener_por_numero(self, numero):
        return self._llamar("obtener_por_numero", numero=numero)

    def otorgar_consentimiento(self, cliente_id):
        return self._llamar("otorgar_consentimiento", cliente_id=cliente_id)

    def solicitar_oferta_hipotecario(self, **kwargs):
        return self._llamar("solicitar_oferta_hipotecario", **kwargs)


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture
def doble():
    anterior = app.state.nucleo
    nucleo = DobleNucleo()
    app.state.nucleo = nucleo
    yield nucleo
    app.state.nucleo = anterior


def _auth(client: TestClient) -> dict:
    return {"Authorization": f"Bearer {customer_token(client)}"}


def _nombres(doble: DobleNucleo) -> list[str]:
    return [llamada["metodo"] for llamada in doble.llamadas]


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_v0_no_llama_al_nucleo(client, doble):
    headers = _auth(client)
    billetera = client.get("/cliente/polizas", headers=headers)
    aviso = client.post("/cliente/siniestros", headers=headers, json=AVISO)
    assert billetera.status_code == 200
    assert billetera.json()["polizas"][0]["numero"] == "POL-88219-CO"
    assert aviso.json()["siniestroId"] == "SIN-441"
    assert doble.llamadas == []


def test_ingreso_v1_autentica_y_emite_cliente(client, doble):
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    )
    assert response.status_code == 200
    cuerpo = response.json()
    assert cuerpo["expiraEn"] == 900
    payload = jwt.decode(cuerpo["accessToken"], secret(), algorithms=["HS256"])
    assert payload["rol"] == "cliente"
    assert doble.llamadas == [
        {"metodo": "autenticar", "correo": "camila@correo.com", "contrasena": "secreto"}
    ]


def test_ingreso_v1_credenciales_invalidas(client, doble):
    doble.respuestas["autenticar"] = HTTPException(status_code=401, detail="no")
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "mal"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Credenciales invalidas"


def test_ingreso_v1_propaga_503(client, doble):
    doble.respuestas["autenticar"] = HTTPException(status_code=503, detail="ms-identidad no disponible")
    response = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    )
    assert response.status_code == 503
    assert response.json()["detail"] == "ms-identidad no disponible"


def test_refresh_v1_no_llama_al_nucleo(client, doble):
    ingreso = client.post(
        "/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    ).json()
    doble.llamadas.clear()
    refrescada = client.post("/v1/sesion/refresh", json={"refreshToken": ingreso["refreshToken"]})
    assert refrescada.status_code == 200
    assert refrescada.json()["expiraEn"] == 900
    assert doble.llamadas == []


def test_salida_v1_no_llama_al_nucleo(client, doble):
    response = client.post("/v1/sesion/salida", headers=_auth(client))
    assert response.json() == {"estado": "aceptada"}
    assert doble.llamadas == []


def test_cotizacion_v1_llama_cotizar_sin_rol(client, doble):
    doble.respuestas["cotizar"] = COTIZACION
    response = client.post(
        "/v1/cliente/cotizaciones",
        headers=_auth(client),
        json={"ramo": "Protección de dispositivo", "datosRiesgo": {"valor": 1}, "rol": "operador"},
    )
    assert response.status_code == 200
    assert response.json()["cotizacionId"] == "COT-9"
    assert "producto" not in response.json()
    llamada = doble.llamadas[0]
    assert llamada["canal"] == "movil"
    assert llamada["producto"] == "proteccion-dispositivo"
    assert llamada["datos_riesgo"] == {"valor": 1}
    assert "rol" not in llamada
    assert llamada["idempotency_key"]


def test_cotizacion_v1_slug_y_cuerpo_incompleto(client, doble):
    headers = _auth(client)
    doble.respuestas["cotizar"] = COTIZACION
    client.post(
        "/v1/cliente/cotizaciones",
        headers=headers,
        json={"ramo": "Vida Extra", "datosRiesgo": {}},
    )
    assert doble.llamadas[-1]["producto"] == "vida-extra"
    doble.respuestas["cotizar"] = {"cotizacion_id": "COT-9"}
    incompleta = client.post(
        "/v1/cliente/cotizaciones",
        headers=headers,
        json={"ramo": "Vida", "datosRiesgo": {}},
    )
    assert incompleta.status_code == 502
    assert incompleta.json()["detail"] == DETALLE_INCOMPLETA


def test_reconsulta_v1(client, doble):
    headers = _auth(client)
    doble.respuestas["reconsultar"] = COTIZACION
    releida = client.get("/v1/cliente/cotizaciones/COT-9", headers=headers)
    assert releida.json()["ramo"] == "vida"
    assert doble.llamadas[-1] == {"metodo": "reconsultar", "cotizacion_id": "COT-9"}
    doble.respuestas["reconsultar"] = {"estado": "oferta_vigente"}
    assert client.get("/v1/cliente/cotizaciones/COT-9", headers=headers).status_code == 502


def test_aceptar_emitida_y_rechazada(client, doble):
    headers = _auth(client)
    doble.respuestas["aceptar_oferta"] = ACEPTADA
    doble.respuestas["cobrar_prima"] = {"id": "pago-1"}
    doble.respuestas["emitir"] = POLIZA
    doble.respuestas["reconsultar"] = COTIZACION
    emitida = client.post("/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-9"})
    assert emitida.json() == {
        "numero": "POL-9",
        "ramo": "vida",
        "estado": "vigente",
        "venceEn": "2027-01-01",
    }
    assert _nombres(doble) == ["aceptar_oferta", "cobrar_prima", "emitir", "reconsultar"]
    assert doble.llamadas[0]["cotizacion_id"] == "COT-9"
    assert doble.llamadas[0]["score"] == "0.5000"
    assert doble.llamadas[2]["coberturas"][0]["nombre"] == "aceptada"

    doble.llamadas.clear()
    doble.respuestas["aceptar_oferta"] = {"decision": "RECHAZADA", "motivo": "fuera de rango"}
    rechazada = client.post(
        "/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-RECHAZADA"}
    )
    assert rechazada.json() == {"estado": "rechazada", "motivo": "fuera de rango"}
    assert _nombres(doble) == ["aceptar_oferta"]


def test_aceptar_incompleta_es_502(client, doble):
    headers = _auth(client)
    doble.respuestas["aceptar_oferta"] = {"resultado": "OTRO"}
    assert (
        client.post("/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-1"}).status_code
        == 502
    )
    doble.respuestas["aceptar_oferta"] = {"decision": "RECHAZADA"}
    assert (
        client.post("/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-1"}).status_code
        == 502
    )
    doble.respuestas["aceptar_oferta"] = {"decision": "aceptada", "prima": "1"}
    assert (
        client.post("/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-1"}).status_code
        == 502
    )
    sin_estado = {**ACEPTADA}
    del sin_estado["estado"]
    doble.respuestas["aceptar_oferta"] = sin_estado
    doble.respuestas["cobrar_prima"] = {"id": "pago-1"}
    doble.respuestas["emitir"] = POLIZA
    doble.respuestas["reconsultar"] = COTIZACION
    client.post("/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-1"})
    assert doble.llamadas[-2]["coberturas"][0]["nombre"] == "cobertura-base"
    doble.respuestas["cobrar_prima"] = {}
    assert (
        client.post("/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-1"}).status_code
        == 502
    )
    doble.respuestas["cobrar_prima"] = {"id": "pago-1"}
    doble.respuestas["emitir"] = {"numero": "POL-9", "estado": "vigente"}
    assert (
        client.post("/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-1"}).status_code
        == 502
    )
    doble.respuestas["emitir"] = POLIZA
    doble.respuestas["reconsultar"] = {"cotizacion_id": "COT-9"}
    assert (
        client.post("/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-1"}).status_code
        == 502
    )


def test_billetera_v1_proyecta_y_degrada(client, doble):
    headers = _auth(client)
    doble.respuestas["listar_polizas"] = [POLIZA]
    doble.respuestas["reconsultar_por_oferta"] = {"producto": "vida"}
    body = client.get("/v1/cliente/polizas", headers=headers).json()
    assert body["polizas"] == [
        {
            "numero": "POL-9",
            "ramo": "vida",
            "resumen": "Robo",
            "estado": "vigente",
            "venceEn": "2027-01-01",
        }
    ]
    assert doble.llamadas[0]["limite"] == 20

    doble.respuestas["reconsultar_por_oferta"] = HTTPException(status_code=404, detail="No existe")
    assert client.get("/v1/cliente/polizas", headers=headers).json()["polizas"][0]["ramo"] == (
        "Sin clasificar"
    )
    doble.respuestas["reconsultar_por_oferta"] = HTTPException(status_code=503, detail="caido")
    assert client.get("/v1/cliente/polizas", headers=headers).status_code == 200

    sin_oferta = dict(POLIZA)
    del sin_oferta["oferta_id"]
    doble.respuestas["listar_polizas"] = [sin_oferta]
    antes = len(doble.llamadas)
    client.get("/v1/cliente/polizas", headers=headers)
    assert _nombres(doble)[antes:] == ["listar_polizas"]

    vacia = dict(POLIZA)
    vacia["coberturas"] = []
    doble.respuestas["listar_polizas"] = [vacia]
    assert (
        client.get("/v1/cliente/polizas", headers=headers).json()["polizas"][0]["resumen"]
        == "Sin coberturas"
    )


def test_billetera_v1_incompleta_es_502(client, doble):
    headers = _auth(client)
    doble.respuestas["listar_polizas"] = {"polizas": []}
    assert client.get("/v1/cliente/polizas", headers=headers).status_code == 502
    doble.respuestas["listar_polizas"] = [{"numero": "POL-1"}]
    assert client.get("/v1/cliente/polizas", headers=headers).status_code == 502
    rota = dict(POLIZA)
    rota["coberturas"] = "no-lista"
    doble.respuestas["listar_polizas"] = [rota]
    assert client.get("/v1/cliente/polizas", headers=headers).status_code == 502
    rota["coberturas"] = ["Robo"]
    assert client.get("/v1/cliente/polizas", headers=headers).status_code == 502
    rota["coberturas"] = [{}]
    assert client.get("/v1/cliente/polizas", headers=headers).status_code == 502
    doble.respuestas["listar_polizas"] = [POLIZA]
    doble.respuestas["reconsultar_por_oferta"] = HTTPException(status_code=422, detail="mal")
    assert client.get("/v1/cliente/polizas", headers=headers).status_code == 422


def test_detalle_v1(client, doble):
    headers = _auth(client)
    doble.respuestas["obtener_por_numero"] = POLIZA
    doble.respuestas["reconsultar_por_oferta"] = {"producto": "vida"}
    detalle = client.get("/v1/cliente/polizas/POL-9", headers=headers).json()
    assert detalle["queHacer"] == "Toma la foto del daño y anota fecha y lugar."
    assert "oferta_id" not in detalle
    assert doble.llamadas[0] == {"metodo": "obtener_por_numero", "numero": "POL-9"}


def test_pagos_e_inicio_siguen_en_muestra(client, doble):
    headers = _auth(client)
    pagos = client.get("/v1/cliente/pagos-automaticos", headers=headers).json()
    assert pagos["siniestroId"] == "SIN-220"
    inicio = client.get("/v1/cliente/inicio", headers=headers).json()
    assert inicio["hipotecario"] is None
    assert doble.llamadas == []


def test_hipoteca_v1(client, doble):
    headers = _auth(client)
    cuerpo = {"credito": {"valor": 1, "plazoMeses": 12}, "consentimientoPerfil": False}
    degradada = client.post("/v1/cliente/oferta-hipotecaria", headers=headers, json=cuerpo)
    assert degradada.json()["degradada"] is True
    assert degradada.json()["prima"] == 50000
    assert doble.llamadas == []

    doble.respuestas["solicitar_oferta_hipotecario"] = {
        "precio": "64000.00",
        "moneda": "COP",
        "degradado": False,
        "factores": [
            {"factor": "plazo", "impacto": "positivo"},
            {"factor": "valor del crédito"},
        ],
    }
    lista = client.post(
        "/v1/cliente/oferta-hipotecaria",
        headers=headers,
        json={**cuerpo, "consentimientoPerfil": True},
    )
    assert lista.json()["prima"] == 64000.0
    assert lista.json()["factores"] == ["plazo", "valor del crédito"]
    assert lista.json()["degradada"] is False
    assert _nombres(doble) == ["otorgar_consentimiento", "solicitar_oferta_hipotecario"]

    doble.respuestas["solicitar_oferta_hipotecario"] = {"precio": "1"}
    assert (
        client.post(
            "/v1/cliente/oferta-hipotecaria",
            headers=headers,
            json={**cuerpo, "consentimientoPerfil": True},
        ).status_code
        == 502
    )
    doble.respuestas["solicitar_oferta_hipotecario"] = {
        "precio": "1",
        "moneda": "COP",
        "degradado": False,
        "factores": "plazo",
    }
    assert (
        client.post(
            "/v1/cliente/oferta-hipotecaria",
            headers=headers,
            json={**cuerpo, "consentimientoPerfil": True},
        ).status_code
        == 502
    )
    doble.respuestas["solicitar_oferta_hipotecario"] = {
        "precio": "1",
        "moneda": "COP",
        "degradado": True,
        "factores": [{}],
    }
    assert (
        client.post(
            "/v1/cliente/oferta-hipotecaria",
            headers=headers,
            json={**cuerpo, "consentimientoPerfil": True},
        ).status_code
        == 502
    )


def test_ruta_mapeada_sin_url_es_503(client):
    anterior = app.state.nucleo
    app.state.nucleo = ClienteNucleo({})
    try:
        response = client.get("/v1/cliente/polizas", headers=_auth(client))
    finally:
        app.state.nucleo = anterior
    assert response.status_code == 503
    assert response.json()["detail"] == "MS_POLIZAS_URL no configurado"


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
    assert doble.llamadas == []


def test_rutas_sin_mapa_no_llaman_y_el_aviso_es_estable(client, doble):
    headers = _auth(client)
    alta = client.post("/v1/registro", json=ALTA)
    assert alta.json()["pruebaDeVida"] == "ok"
    assert client.post("/v1/registro/consentimiento", json={"habeasData": False}).json() == {
        "habeasData": False
    }
    primero = client.post("/v1/cliente/siniestros", headers=headers, json=AVISO)
    segundo = client.post("/v1/cliente/siniestros", headers=headers, json=AVISO)
    assert primero.json()["siniestroId"] == "SIN-441"
    assert segundo.json()["siniestroId"] == "SIN-441"
    assert client.get("/v1/cliente/siniestros", headers=headers).status_code == 200
    assert client.get("/v1/cliente/avisos", headers=headers).status_code == 200
    assert (
        client.post(
            "/v1/cliente/avisos/token",
            headers=headers,
            json={"token": "fcm", "plataforma": "android"},
        ).status_code
        == 200
    )
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


def test_rutas_equivocadas_del_cliente_no_existen(client):
    headers = _auth(client)
    assert client.post("/registro/revocacion", json={"habeasData": False}).status_code == 404
    assert client.post("/cliente/push", headers=headers).status_code == 404
    assert client.post("/cliente/polizas/POL-1/ciclo", headers=headers).status_code == 404
    assert client.post("/v1/operador/polizas/ciclo", headers=headers).status_code == 404


def test_cliente_real_sin_url_no_abre_socket():
    cliente = ClienteNucleo({"ms-polizas": "  "})
    with pytest.raises(HTTPException) as exc:
        cliente.listar_polizas(usuario_id="u", limite=1)
    assert exc.value.detail == "MS_POLIZAS_URL no configurado"


class _Respuesta:
    def __init__(self, status, payload, text="plano"):
        self.status_code = status
        self._payload = payload
        self.text = text

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


def test_cliente_http_traduce_exito_y_errores(monkeypatch):
    visto = {}

    class Falso:
        def __init__(self, *, base_url, timeout):
            visto["base"] = base_url
            visto["timeout"] = timeout

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def request(self, metodo, ruta, json=None, params=None, headers=None):
            visto["llamada"] = (metodo, ruta, json, params, headers)
            if isinstance(self.respuesta, Exception):
                raise self.respuesta
            return self.respuesta

    monkeypatch.setattr("app.clients.nucleo.httpx.Client", Falso)
    cliente = ClienteNucleo(
        {
            "ms-identidad": " http://ms-identidad:8080/ ",
            "ms-cotizacion": "http://ms-cotizacion:8000",
            "ms-pagos": "http://ms-pagos:8080",
            "ms-polizas": "http://ms-polizas:8080",
            "ms-perfilamiento": "http://ms-perfilamiento:8080",
        }
    )
    Falso.respuesta = _Respuesta(200, {"ok": True})
    assert cliente.autenticar(correo="a@b.c", contrasena="s") == {"ok": True}
    assert visto["base"] == "http://ms-identidad:8080"
    assert visto["llamada"][4] == {}

    Falso.respuesta = _Respuesta(201, [{"numero": "POL-1"}])
    assert cliente.listar_polizas(usuario_id="u", limite=20)[0]["numero"] == "POL-1"
    assert visto["llamada"][3] == {"usuario_id": "u", "limite": 20}

    Falso.respuesta = _Respuesta(200, {"cotizacion_id": "c"})
    assert cliente.cotizar(
        idempotency_key="k",
        usuario_id="u",
        socio_id="s",
        consentimiento_id="c",
        producto="vida",
        canal="movil",
        datos_riesgo={},
    )["cotizacion_id"] == "c"
    assert visto["llamada"][4]["Idempotency-Key"] == "k"

    Falso.respuesta = _Respuesta(401, {"mensaje": "no"})
    with pytest.raises(HTTPException) as exc:
        cliente.autenticar(correo="a@b.c", contrasena="s")
    assert exc.value.status_code == 401 and exc.value.detail == "no"

    Falso.respuesta = _Respuesta(422, {"codigo": "rechazado"})
    with pytest.raises(HTTPException) as exc:
        cliente.reconsultar("x")
    assert exc.value.detail == {"codigo": "rechazado"}

    Falso.respuesta = _Respuesta(409, ["ya"])
    with pytest.raises(HTTPException) as exc:
        cliente.otorgar_consentimiento("c")
    assert exc.value.status_code == 409 and exc.value.detail == ["ya"]

    Falso.respuesta = _Respuesta(401, ValueError("no json"))
    with pytest.raises(HTTPException) as exc:
        cliente.autenticar(correo="a@b.c", contrasena="s")
    assert exc.value.detail == "Operación rechazada"

    Falso.respuesta = _Respuesta(404, {})
    with pytest.raises(HTTPException) as exc:
        cliente.obtener_por_numero("POL-1")
    assert exc.value.status_code == 404

    Falso.respuesta = _Respuesta(500, {"error": True})
    with pytest.raises(HTTPException) as exc:
        cliente.reconsultar_por_oferta("o")
    assert exc.value.detail == "ms-cotizacion no disponible"

    Falso.respuesta = _Respuesta(200, ValueError("no json"))
    with pytest.raises(HTTPException) as exc:
        cliente.aceptar_oferta(cotizacion_id="c", idempotency_key="k", perfil_id="p", score="0.5")
    assert exc.value.status_code == 502

    Falso.respuesta = httpx_connect_error()
    with pytest.raises(HTTPException) as exc:
        cliente.cobrar_prima(
            solicitud_id="s",
            oferta_id="o",
            usuario_id="u",
            monto="1",
            token_medio_pago="t",
        )
    assert exc.value.detail == "ms-pagos no disponible"

    Falso.respuesta = _Respuesta(200, {"id": "p"})
    assert cliente.emitir(
        solicitud_id="s",
        oferta_id="o",
        usuario_id="u",
        token_pago_confirmado="p",
        coberturas=[],
    )["id"] == "p"
    assert cliente.solicitar_oferta_hipotecario(idempotency_key="k", cliente_id="c")["id"] == "p"


def httpx_connect_error():
    import httpx

    return httpx.ConnectError("sin red")


def test_refresh_y_salida_de_la_edicion_actual(client, doble):
    ingreso = client.post(
        "/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    ).json()
    refrescada = client.post("/sesion/refresh", json={"refreshToken": ingreso["refreshToken"]})
    assert refrescada.json()["expiraEn"] == 900
    salida = client.post(
        "/sesion/salida",
        headers={"Authorization": f"Bearer {ingreso['accessToken']}"},
    )
    assert salida.json() == {"estado": "aceptada"}
    assert doble.llamadas == []


def test_aceptar_v0_devuelve_la_muestra(client):
    body = client.post(
        "/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": "COT-1"},
    ).json()
    assert body["numero"] == "POL-88219-CO"


def test_token_invalido_y_refresh_como_acceso(client):
    assert (
        client.get("/cliente/inicio", headers={"Authorization": "Bearer no-es-jwt"}).status_code
        == 401
    )
    ingreso = client.post(
        "/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    ).json()
    como_acceso = client.get(
        "/cliente/inicio",
        headers={"Authorization": f"Bearer {ingreso['refreshToken']}"},
    )
    assert como_acceso.status_code == 401
    como_refresh = client.post("/sesion/refresh", json={"refreshToken": ingreso["accessToken"]})
    assert como_refresh.status_code == 401
    ajeno = jwt.encode(
        {
            "sub": "desk@solventa.com",
            "rol": "asesor",
            "typ": "refresh",
            "exp": 9_999_999_999,
        },
        "test-secret",
        algorithm="HS256",
    )
    assert client.post("/sesion/refresh", json={"refreshToken": ajeno}).status_code == 401


def test_sin_secreto_es_500(monkeypatch, client):
    monkeypatch.delenv("SOLVENTA_TOKEN_SECRET", raising=False)
    response = client.get("/cliente/inicio", headers={"Authorization": "Bearer x"})
    assert response.status_code == 500
    assert response.json()["detail"] == "SOLVENTA_TOKEN_SECRET no configurado"


def test_revocacion_exige_habeas_falso(client):
    response = client.post("/registro/consentimiento", json={"habeasData": True})
    assert response.status_code == 400


def test_asistencia_sin_prestador_es_400(client):
    response = client.post(
        "/cliente/asistencias",
        headers=_auth(client),
        json={
            "prestadorId": "",
            "geo": {"lat": 4.65, "lng": -74.08, "precisionM": 12},
            "poliza": "POL-1",
        },
    )
    assert response.status_code == 400


def test_v0_rechaza_cotizacion(client):
    body = client.post(
        "/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": "COT-RECHAZADA"},
    ).json()
    assert body["estado"] == "rechazada"
