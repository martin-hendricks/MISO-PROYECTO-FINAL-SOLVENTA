import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.clients.nucleo import DETALLE_INCOMPLETA, ClienteNucleo, token_saliente
from app.dependencies import secret
from app.main import app
from app.routers.cliente import _contexto

def _dueno() -> dict:
    return _contexto({"uid": UID, "sub": "camila@correo.com"})
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
    "ingresos_mensuales": "4500000.00",
    "gastos_mensuales": "1500000.00",
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
    "inicio_vigencia": "2026-01-01",
    "fin_vigencia": "2027-01-01",
    "oferta_id": "oferta-1",
    "coberturas": [{"nombre": "Robo", "suma_asegurada": "40000000.00", "deducible": "0"}],
    "renovable": True,
    "renovacion_automatica": False,
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
        self.tokens: list[str | None] = []
        self.respuestas: dict = {}

    def _llamar(self, nombre: str, **kwargs):
        self.tokens.append(token_saliente.get())
        self.llamadas.append({"metodo": nombre, **kwargs})
        valor = self.respuestas.get(nombre, {})
        if isinstance(valor, Exception):
            raise valor
        return valor

    def autenticar(self, *, correo, contrasena):
        valor = self.respuestas.get("autenticar")
        self.llamadas.append({"metodo": "autenticar", "correo": correo, "contrasena": contrasena})
        if isinstance(valor, Exception):
            raise valor
        if valor is None:
            return {
                "usuario_id": "11111111-1111-1111-1111-111111111111",
                "email": correo.strip().lower(),
                "estado": "ACTIVO",
            }
        return valor

    def crear_usuario(
        self,
        *,
        tipo_documento,
        numero_documento,
        email,
        password,
        nombre="",
        apellidos="",
        ingresos_mensuales=None,
        gastos_mensuales=None,
    ):
        valor = self.respuestas.get("crear_usuario")
        self.llamadas.append(
            {
                "metodo": "crear_usuario",
                "tipo_documento": tipo_documento,
                "numero_documento": numero_documento,
                "email": email,
                "password": password,
                "nombre": nombre,
                "apellidos": apellidos,
                "ingresos_mensuales": ingresos_mensuales,
                "gastos_mensuales": gastos_mensuales,
            }
        )
        if isinstance(valor, Exception):
            raise valor
        if valor is None:
            return {
                "usuario_id": "11111111-1111-1111-1111-111111111111",
                "email": email.strip().lower(),
                "estado": "ACTIVO",
                "nombre": nombre,
                "apellidos": apellidos,
            }
        return valor

    def cotizar(self, **kwargs):
        return self._llamar("cotizar", **kwargs)

    def reconsultar(self, cotizacion_id, usuario_id=None):
        return self._llamar("reconsultar", cotizacion_id=cotizacion_id, usuario_id=usuario_id)

    def reconsultar_por_oferta(self, oferta_id):
        return self._llamar("reconsultar_por_oferta", oferta_id=oferta_id)

    def aceptar_oferta(self, **kwargs):
        return self._llamar("aceptar_oferta", **kwargs)

    def cobrar_prima(self, **kwargs):
        return self._llamar("cobrar_prima", **kwargs)

    def emitir(self, **kwargs):
        return self._llamar("emitir", **kwargs)

    def listar_cotizaciones_usuario(self, *, usuario_id, tamano):
        return self._llamar("listar_cotizaciones_usuario", usuario_id=usuario_id, tamano=tamano)

    def listar_polizas(self, **kwargs):
        return self._llamar("listar_polizas", **kwargs)

    def obtener_por_numero(self, numero, usuario_id=None):
        valor = self._llamar("obtener_por_numero", numero=numero, usuario_id=usuario_id)
        if valor == {}:
            return {"id": "11111111-1111-1111-1111-111111111111", "numero": numero, "usuario_id": usuario_id}
        return valor

    def guardar_preferencia(self, poliza_id, renovacion_automatica, usuario_id):
        return self._llamar(
            "guardar_preferencia",
            poliza_id=poliza_id,
            renovacion_automatica=renovacion_automatica,
            usuario_id=usuario_id,
        ) or {"numero": poliza_id, "renovacion_automatica": renovacion_automatica}

    def listar_siniestros(self, *, usuario_id):
        return self._llamar("listar_siniestros", usuario_id=usuario_id) or []

    def registrar_aviso(self, *, usuario_id, datos, archivos, idempotency_key):
        return self._llamar(
            "registrar_aviso",
            usuario_id=usuario_id,
            datos=datos,
            idempotency_key=idempotency_key,
            archivos=len(archivos),
        ) or {
            "siniestro": {
                "id": "66666666-6666-6666-6666-666666666666",
                "numero": "66666666-6666-6666-6666-666666666666",
                "estado": "recibido",
            }
        }

    def detalle_siniestro(self, siniestro_id, usuario_id):
        valor = self._llamar("detalle_siniestro", siniestro_id=siniestro_id, usuario_id=usuario_id)
        if not valor:
            raise HTTPException(status_code=404, detail="No existe")
        return valor

    def crear_siniestro(self, *, usuario_id, poliza, poliza_id, idempotency_key):
        return self._llamar(
            "crear_siniestro",
            usuario_id=usuario_id,
            poliza=poliza,
            poliza_id=poliza_id,
            idempotency_key=idempotency_key,
        ) or {
            "id": "66666666-6666-6666-6666-666666666666",
            "estado": "recibido",
        }

    def obtener_usuario(self, usuario_id):
        return self._llamar("obtener_usuario", usuario_id=usuario_id)

    def actualizar_perfil(self, usuario_id, *, nombre, apellidos):
        self.llamadas.append(
            {
                "metodo": "actualizar_perfil",
                "usuario_id": usuario_id,
                "nombre": nombre,
                "apellidos": apellidos,
            }
        )
        valor = self.respuestas.get("actualizar_perfil", {})
        if isinstance(valor, Exception):
            raise valor
        return valor

    def otorgar_consentimiento(self, cliente_id):
        return self._llamar("otorgar_consentimiento", cliente_id=cliente_id)

    def solicitar_oferta_hipotecario(self, **kwargs):
        return self._llamar("solicitar_oferta_hipotecario", **kwargs)

    def polizas_por_vencer(self, **kwargs):
        return self._llamar("polizas_por_vencer", **kwargs) or []

    def registrar_dispositivo(self, **kwargs):
        return self._llamar("registrar_dispositivo", **kwargs) or {
            "dispositivo_id": "77777777-7777-7777-7777-777777777777",
            "activo": True,
        }


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


UID = "11111111-1111-1111-1111-111111111111"


def _auth(client: TestClient) -> dict:
    headers = {"Authorization": f"Bearer {customer_token(client)}"}
    nucleo = getattr(client.app.state, "nucleo", None)
    if hasattr(nucleo, "llamadas"):
        nucleo.llamadas.clear()
    return headers


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
        json={"correo": "Camila@Correo.com", "contrasena": "secreto"},
    )
    assert response.status_code == 200
    cuerpo = response.json()
    assert cuerpo["expiraEn"] == 900
    payload = jwt.decode(cuerpo["accessToken"], secret(), algorithms=["HS256"])
    assert payload["rol"] == "cliente"
    assert payload["uid"] == UID
    assert payload["sub"] == "camila@correo.com"
    assert doble.llamadas == [
        {"metodo": "autenticar", "correo": "Camila@Correo.com", "contrasena": "secreto"}
    ]


def test_ingreso_v1_rechaza_respuesta_rota_o_cuenta_inactiva(client, doble):
    doble.respuestas["autenticar"] = []
    rota = client.post("/v1/sesion/ingreso", json={"correo": "a@b.c", "contrasena": "s"})
    assert rota.status_code == 502

    doble.respuestas["autenticar"] = {"estado": "INACTIVO", "email": "a@b.c", "usuario_id": UID}
    inactiva = client.post("/v1/sesion/ingreso", json={"correo": "a@b.c", "contrasena": "s"})
    assert inactiva.status_code == 401

    doble.respuestas["autenticar"] = {"estado": "ACTIVO", "email": "a@b.c"}
    sin_id = client.post("/v1/sesion/ingreso", json={"correo": "a@b.c", "contrasena": "s"})
    assert sin_id.status_code == 401


def test_ingreso_bff_movil_prefix_autentica_igual_que_v1(client, doble):
    # /bff-movil/v1/*: el ALB distingue bff-movil de bff-web por este prefijo
    # propio (ver infra/terraform/environments/minimo/variables.tf), ya que
    # ambos BFF comparten los mismos paths /v1/* y el ALB solo enruta por
    # path. El pod responde al path completo tal cual, sin que el ALB lo
    # recorte -- este test confirma que ese tercer router registrado existe
    # y se comporta igual que /v1/sesion/ingreso.
    response = client.post(
        "/bff-movil/v1/sesion/ingreso",
        json={"correo": "camila@correo.com", "contrasena": "secreto"},
    )
    assert response.status_code == 200
    payload = jwt.decode(response.json()["accessToken"], secret(), algorithms=["HS256"])
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


def test_cotizacion_bff_movil_prefix_llama_cotizar(client, doble):
    doble.respuestas["cotizar"] = COTIZACION
    response = client.post(
        "/bff-movil/v1/cliente/cotizaciones",
        headers=_auth(client),
        json={"ramo": "Protección de dispositivo", "datosRiesgo": {"valor": 1}},
    )
    assert response.status_code == 200
    assert response.json()["cotizacionId"] == "COT-9"
    cotizar = next(llamada for llamada in doble.llamadas if llamada["metodo"] == "cotizar")
    assert cotizar["producto"] == "proteccion-dispositivo"


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
    llamada = next(item for item in doble.llamadas if item["metodo"] == "cotizar")
    assert llamada["canal"] == "movil"
    assert llamada["producto"] == "proteccion-dispositivo"
    assert llamada["datos_riesgo"] == {"valor": 1}
    assert "rol" not in llamada
    assert llamada["idempotency_key"]


def test_cotizacion_v1_slug_y_cuerpo_incompleto(client, doble):
    headers = _auth(client)
    doble.respuestas["cotizar"] = COTIZACION
    desconocido = client.post(
        "/v1/cliente/cotizaciones",
        headers=headers,
        json={"ramo": "Vida Extra", "datosRiesgo": {}},
    )
    assert desconocido.status_code == 404
    assert doble.llamadas == []
    doble.respuestas["cotizar"] = {"cotizacion_id": "COT-9"}
    incompleta = client.post(
        "/v1/cliente/cotizaciones",
        headers=headers,
        json={"ramo": "Protección de dispositivo", "datosRiesgo": {}},
    )
    assert incompleta.status_code == 502
    assert incompleta.json()["detail"] == DETALLE_INCOMPLETA


def test_reconsulta_v1(client, doble):
    headers = _auth(client)
    doble.respuestas["reconsultar"] = COTIZACION
    releida = client.get("/v1/cliente/cotizaciones/COT-9", headers=headers)
    assert releida.json()["ramo"] == "Sin clasificar"
    assert releida.json()["descripcion"] == ""
    assert doble.llamadas[-1] == {
        "metodo": "reconsultar",
        "cotizacion_id": "COT-9",
        "usuario_id": UID,
    }
    doble.respuestas["reconsultar"] = {"estado": "oferta_vigente"}
    assert client.get("/v1/cliente/cotizaciones/COT-9", headers=headers).status_code == 502


def test_aceptar_cotizacion_rechaza_datos_de_tarjeta(client):
    headers = {**_auth(client), "Idempotency-Key": "clave-aceptar-01"}
    respuesta = client.post(
        "/v1/cliente/cotizaciones/COT-9/aceptacion",
        headers=headers,
        json={"numeroTarjeta": "4242424242424242"},
    )
    assert respuesta.status_code == 422


def test_aceptar_cotizacion_v1_emite_la_poliza(client, doble):
    headers = {**_auth(client), "Idempotency-Key": "clave-aceptar-01"}
    doble.respuestas["aceptar_oferta"] = {**ACEPTADA, "moneda": "COP"}
    doble.respuestas["cobrar_prima"] = {"id": "pago-1"}
    doble.respuestas["emitir"] = POLIZA
    doble.respuestas["reconsultar"] = COTIZACION

    respuesta = client.post("/v1/cliente/cotizaciones/COT-9/aceptacion", headers=headers)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "cotizacionId": "COT-9",
        "estado": "aceptada",
        "prima": "10.00",
        "moneda": "COP",
        "poliza": {
            "numero": "POL-9",
            "ramo": "Sin clasificar",
            "descripcion": "",
            "estado": "vigente",
            "venceEn": "2027-01-01",
        },
    }
    assert _nombres(doble) == ["aceptar_oferta", "cobrar_prima", "emitir", "reconsultar"]
    assert doble.llamadas[0] == {
        "metodo": "aceptar_oferta",
        "cotizacion_id": "COT-9",
        "idempotency_key": "clave-aceptar-01",
        "perfil_id": _dueno()["perfil_id"],
        "score": "0.5000",
        "usuario_id": UID,
    }
    assert doble.llamadas[1]["usuario_id"] == _dueno()["usuario_id"]
    assert doble.llamadas[1]["token_medio_pago"] == "stub-medio-pago"
    assert doble.llamadas[2]["token_pago_confirmado"] == "pago-1"

    doble.llamadas.clear()
    prefijo = client.post("/bff-movil/v1/cliente/cotizaciones/COT-9/aceptacion", headers=headers)
    assert prefijo.status_code == 200
    assert prefijo.json()["estado"] == "aceptada"
    assert prefijo.json()["poliza"]["numero"] == "POL-9"
    assert doble.llamadas[0]["idempotency_key"] == "clave-aceptar-01"


def test_aceptar_cotizacion_rechazada_no_emite(client, doble):
    headers = {**_auth(client), "Idempotency-Key": "clave-aceptar-01"}
    doble.respuestas["aceptar_oferta"] = {"decision": "RECHAZADA", "motivo": "fuera de rango"}

    respuesta = client.post("/v1/cliente/cotizaciones/COT-9/aceptacion", headers=headers)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"estado": "rechazada", "motivo": "fuera de rango"}
    assert _nombres(doble) == ["aceptar_oferta"]


def test_aceptar_cotizacion_sin_version_es_404(client, doble):
    headers = {**_auth(client), "Idempotency-Key": "clave-aceptar-01"}
    respuesta = client.post("/cliente/cotizaciones/COT-9/aceptacion", headers=headers)
    assert respuesta.status_code == 404
    assert doble.llamadas == []


def test_aceptar_cotizacion_clave_invalida_es_422(client, doble):
    token = _auth(client)
    sin_clave = client.post("/v1/cliente/cotizaciones/COT-9/aceptacion", headers=token)
    corta = client.post(
        "/v1/cliente/cotizaciones/COT-9/aceptacion",
        headers={**token, "Idempotency-Key": "corta"},
    )
    assert sin_clave.status_code == 422
    assert corta.status_code == 422
    assert doble.llamadas == []


def test_aceptar_cotizacion_incompleta_es_502(client, doble):
    headers = {**_auth(client), "Idempotency-Key": "clave-aceptar-01"}
    doble.respuestas["aceptar_oferta"] = {"cotizacion_id": "COT-9", "estado": "aceptada", "prima": "10.00"}
    respuesta = client.post("/v1/cliente/cotizaciones/COT-9/aceptacion", headers=headers)
    assert respuesta.status_code == 502
    assert respuesta.json()["detail"] == DETALLE_INCOMPLETA
    assert _nombres(doble) == ["aceptar_oferta"]
    doble.llamadas.clear()
    doble.respuestas["aceptar_oferta"] = {"decision": "RECHAZADA"}
    assert client.post("/v1/cliente/cotizaciones/COT-9/aceptacion", headers=headers).status_code == 502
    assert _nombres(doble) == ["aceptar_oferta"]


def test_aceptar_emitida_y_rechazada(client, doble):
    headers = _auth(client)
    doble.respuestas["aceptar_oferta"] = ACEPTADA
    doble.respuestas["cobrar_prima"] = {"id": "pago-1"}
    doble.respuestas["emitir"] = POLIZA
    doble.respuestas["reconsultar"] = COTIZACION
    emitida = client.post("/v1/cliente/polizas", headers=headers, json={"cotizacionId": "COT-9"})
    assert emitida.json() == {
        "numero": "POL-9",
        "ramo": "Sin clasificar",
        "descripcion": "",
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
            "ramo": "Sin clasificar",
            "descripcion": "",
            "resumen": "Robo",
            "estado": "VIGENTE",
            "venceEn": "2027-01-01",
            "inicioVigencia": "2026-01-01",
            "finVigencia": "2027-01-01",
            "moneda": "",
            "primaTotal": 0.0,
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
    assert detalle["inicioVigencia"] == "2026-01-01"
    assert detalle["finVigencia"] == "2027-01-01"
    assert detalle["estado"] == "VIGENTE"
    assert detalle["primaTotal"] == 0.0
    assert detalle["coberturas"] == [{"nombre": "Robo", "sumaAsegurada": 40000000.0, "deducible": 0.0}]
    assert detalle["renovable"] is True
    assert detalle["renovacionAutomatica"] is False
    assert "cancelacion" not in detalle
    assert "oferta_id" not in detalle
    cancelada = {
        **POLIZA,
        "estado": "cancelada",
        "motivo_cancelacion": "A solicitud del cliente",
        "cancelada_en": "2026-06-01",
        "devolucion_estimada": "12000.50",
        "cancelada_por": "operador",
        "hash_firma_legal": "abc",
    }
    doble.respuestas["obtener_por_numero"] = cancelada
    doble.respuestas["reconsultar_por_oferta"] = {"producto": "soat-motocicleta", "prima": "89000.00", "moneda": "COP"}
    baja = client.get("/v1/cliente/polizas/POL-9", headers=headers).json()
    assert baja["ramo"] == "SOAT motocicleta"
    assert baja["primaTotal"] == 89000.0
    assert baja["moneda"] == "COP"
    assert baja["cancelacion"] == {
        "motivo": "A solicitud del cliente",
        "canceladaEn": "2026-06-01",
        "devolucionEstimada": 12000.5,
    }
    assert "cancelada_por" not in baja
    assert "hash_firma_legal" not in baja
    assert doble.llamadas[0] == {
        "metodo": "obtener_por_numero",
        "numero": "POL-9",
        "usuario_id": UID,
    }


def test_pagos_siguen_en_muestra_e_inicio_toma_la_primera_poliza(client, doble):
    headers = _auth(client)
    pagos = client.get("/v1/cliente/pagos-automaticos", headers=headers).json()
    assert pagos["siniestroId"] == "SIN-220"
    assert doble.llamadas == []

    doble.respuestas["listar_cotizaciones_usuario"] = {
        "items": [
            {"cotizacion_id": "COT-9", "producto": "proteccion-dispositivo"},
            {"cotizacion_id": "COT-8", "producto": "soat-motocicleta"},
        ]
    }
    doble.respuestas["listar_polizas"] = [POLIZA]
    doble.respuestas["reconsultar_por_oferta"] = {"producto": "vida"}
    inicio = client.get("/v1/cliente/inicio", headers=headers).json()
    pendiente = {"cotizacionId": "COT-9", "ramo": "Protección de dispositivo", "estado": "oferta_vigente"}
    assert inicio["hipotecario"] is None
    assert inicio["cotizacionesPendientes"] == [
        pendiente,
        {"cotizacionId": "COT-8", "ramo": "SOAT motocicleta", "estado": "oferta_vigente"},
    ]
    assert inicio["ofertaVigente"] == pendiente
    assert inicio["siniestroEnCurso"] is None
    assert inicio["poliza"] == {"numero": "POL-9", "ramo": "Sin clasificar", "estado": "VIGENTE"}
    cotizaciones = next(llamada for llamada in doble.llamadas if llamada["metodo"] == "listar_cotizaciones_usuario")
    polizas = next(llamada for llamada in doble.llamadas if llamada["metodo"] == "listar_polizas")
    assert cotizaciones["usuario_id"] == _dueno()["usuario_id"]
    assert cotizaciones["tamano"] == 20
    assert polizas["limite"] == 20
    assert doble.tokens
    assert set(doble.tokens) == {headers["Authorization"].removeprefix("Bearer ")}

    doble.llamadas.clear()
    doble.respuestas["listar_cotizaciones_usuario"] = {"items": []}
    doble.respuestas["listar_polizas"] = []
    vacio = client.get("/bff-movil/v1/cliente/inicio", headers=headers).json()
    assert vacio["poliza"] is None
    assert vacio["ofertaVigente"] is None
    assert vacio["cotizacionesPendientes"] == []
    assert any(llamada["metodo"] == "listar_cotizaciones_usuario" for llamada in doble.llamadas)
    assert any(llamada["metodo"] == "listar_polizas" for llamada in doble.llamadas)

    doble.respuestas["listar_cotizaciones_usuario"] = {}
    assert client.get("/v1/cliente/inicio", headers=headers).json()["ofertaVigente"] is None
    doble.respuestas["listar_cotizaciones_usuario"] = {"items": [{"cotizacion_id": "COT-9"}]}
    assert client.get("/v1/cliente/inicio", headers=headers).json()["ofertaVigente"] is None


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
    headers = _auth(client)
    anterior = app.state.nucleo
    app.state.nucleo = ClienteNucleo({})
    try:
        response = client.get("/v1/cliente/polizas", headers=headers)
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


def test_registro_v1_crea_el_usuario_sin_eco_de_contrasena(client, doble):
    response = client.post(
        "/v1/registro",
        json={
            **ALTA,
            "pruebaDeVida": "no",
            "habeasData": False,
            "contrasena": "secreto12",
            "tipoDocumento": "CC",
        },
    )
    assert response.status_code == 200
    cuerpo = response.json()
    assert "contrasena" not in cuerpo
    assert cuerpo["pruebaDeVida"] == "no"
    assert cuerpo["habeasData"] is False
    assert cuerpo["tipoDocumento"] == "CC"
    assert doble.llamadas == [
        {
            "metodo": "crear_usuario",
            "tipo_documento": "CC",
            "numero_documento": "1012345678",
            "email": "camila@correo.com",
            "password": "secreto12",
            "nombre": "Camila",
            "apellidos": "Restrepo",
            "ingresos_mensuales": "4500000.00",
            "gastos_mensuales": "1500000.00",
        }
    ]


def test_registro_sin_version_con_contrasena_crea_el_usuario(client, doble):
    response = client.post(
        "/registro",
        json={**ALTA, "contrasena": "secreto12", "tipoDocumento": "CC"},
    )
    assert response.status_code == 200
    cuerpo = response.json()
    assert "contrasena" not in cuerpo
    assert cuerpo["tipoDocumento"] == "CC"
    assert doble.llamadas == [
        {
            "metodo": "crear_usuario",
            "tipo_documento": "CC",
            "numero_documento": "1012345678",
            "email": "camila@correo.com",
            "password": "secreto12",
            "nombre": "Camila",
            "apellidos": "Restrepo",
            "ingresos_mensuales": "4500000.00",
            "gastos_mensuales": "1500000.00",
        }
    ]


def test_registro_sin_version_sin_contrasena_no_llama_al_nucleo(client, doble):
    response = client.post("/registro", json=ALTA)
    assert response.status_code == 200
    cuerpo = response.json()
    assert cuerpo["pruebaDeVida"] == "ok"
    assert "contrasena" not in cuerpo
    assert "tipoDocumento" not in cuerpo
    assert doble.llamadas == []


def test_registro_v1_cuenta_existente_es_409(client, doble):
    doble.respuestas["crear_usuario"] = HTTPException(status_code=409, detail="duplicada")
    response = client.post(
        "/v1/registro",
        json={**ALTA, "contrasena": "secreto12", "tipoDocumento": "CC"},
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "La cuenta ya existe"


def test_rutas_sin_mapa_no_llaman_y_el_aviso_es_estable(client, doble):
    headers = _auth(client)
    assert client.post("/v1/registro/consentimiento", json={"habeasData": False}).json() == {
        "habeasData": False
    }
    aviso_headers = {**headers, "Idempotency-Key": "aviso-estable-01"}
    aviso = {
        "data": {
            "poliza": "POL-88219-CO",
            "fechaHecho": "2026-03-12",
            "descripcion": "Pantalla rota",
            "lugar": "Calle 72",
        },
        "files": [("archivos", ("dano.png", b"png", "image/png"))],
    }
    primero = client.post("/v1/cliente/siniestros", headers=aviso_headers, **aviso)
    segundo = client.post("/v1/cliente/siniestros", headers=aviso_headers, **aviso)
    assert primero.status_code == 200, primero.text
    assert primero.json()["siniestroId"] == "66666666-6666-6666-6666-666666666666"
    assert segundo.json()["siniestroId"] == "66666666-6666-6666-6666-666666666666"
    assert primero.json()["estado"] == "recibido"
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
    assert [llamada["metodo"] for llamada in doble.llamadas] == [
        "obtener_por_numero",
        "registrar_aviso",
        "obtener_por_numero",
        "registrar_aviso",
        "listar_siniestros",
        "polizas_por_vencer",
        "registrar_dispositivo",
    ]


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

        def request(self, metodo, ruta, json=None, params=None, headers=None, data=None, files=None):
            visto["llamada"] = (metodo, ruta, json, params, headers)
            visto["data"] = data
            visto["files"] = files
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
            "ms-siniestros": "http://ms-siniestros:8080",
        }
    )
    Falso.respuesta = _Respuesta(200, {"ok": True})
    assert cliente.autenticar(correo="a@b.c", contrasena="s") == {"ok": True}
    assert visto["base"] == "http://ms-identidad:8080"
    assert visto["llamada"][4] == {}

    Falso.respuesta = _Respuesta(201, [{"numero": "POL-1"}])
    assert cliente.listar_polizas(usuario_id="u", limite=20)[0]["numero"] == "POL-1"
    assert visto["llamada"][3] == {"usuario_id": "u", "limite": 20}

    Falso.respuesta = _Respuesta(200, {"usuario_id": "u", "email": "a@b.c"})
    assert cliente.obtener_usuario("u")["email"] == "a@b.c"
    assert cliente.actualizar_perfil("u", nombre="Ana", apellidos="Lopez")["email"] == "a@b.c"
    Falso.respuesta = _Respuesta(200, [{"id": "s"}])
    assert cliente.listar_siniestros(usuario_id="u") == [{"id": "s"}]
    Falso.respuesta = _Respuesta(200, {"no": "lista"})
    assert cliente.listar_siniestros(usuario_id="u") == []
    Falso.respuesta = _Respuesta(201, {"id": "s"})
    assert cliente.crear_siniestro(
        usuario_id="u", poliza="POL-1", poliza_id="p", idempotency_key="clave-aviso"
    )["id"] == "s"
    Falso.respuesta = _Respuesta(201, {"siniestro": {"id": "s", "estado": "recibido"}})
    assert cliente.registrar_aviso(
        usuario_id="u",
        datos={"lugar": "Calle 72"},
        archivos=[("dano.png", b"png", "image/png")],
        idempotency_key="clave-aviso-01",
    )["siniestro"]["id"] == "s"
    assert visto["files"] == [("archivos", ("dano.png", b"png", "image/png"))]
    assert visto["data"] == {"datos": '{"lugar": "Calle 72"}'}
    Falso.respuesta = _Respuesta(200, {"numero": "POL-1"})
    assert cliente.obtener_por_numero("POL-1", "u")["numero"] == "POL-1"

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
    assert [llamada["metodo"] for llamada in doble.llamadas] == ["autenticar"]


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


def test_contexto_sin_uid_es_401():
    with pytest.raises(HTTPException) as exc:
        _contexto({})
    assert exc.value.status_code == 401


def test_reconsulta_y_detalle_ajenos_son_404(client, doble):
    headers = _auth(client)
    ajeno = "22222222-2222-2222-2222-222222222222"
    doble.respuestas["reconsultar"] = {**COTIZACION, "usuario_id": ajeno}
    assert client.get("/v1/cliente/cotizaciones/COT-9", headers=headers).status_code == 404
    doble.respuestas["obtener_por_numero"] = {**POLIZA, "usuario_id": ajeno}
    assert client.get("/v1/cliente/polizas/POL-9", headers=headers).status_code == 404


def test_inicio_v1_proyecta_el_siniestro_o_lo_omite_si_el_nucleo_falla(client, doble):
    headers = _auth(client)
    doble.respuestas["listar_cotizaciones_usuario"] = {"items": []}
    doble.respuestas["listar_polizas"] = []
    doble.respuestas["listar_siniestros"] = [{"id": "SIN-1", "estado": "recibido"}]
    inicio = client.get("/v1/cliente/inicio", headers=headers).json()
    assert inicio["siniestroEnCurso"] == {"siniestroId": "SIN-1", "estado": "recibido"}

    doble.respuestas["listar_siniestros"] = HTTPException(status_code=503, detail="caido")
    assert client.get("/v1/cliente/inicio", headers=headers).json()["siniestroEnCurso"] is None


def test_perfil_v1_lee_y_guarda_y_v0_no_existe(client, doble):
    headers = _auth(client)
    doble.respuestas["obtener_usuario"] = {
        "usuario_id": UID,
        "email": "camila@correo.com",
        "nombre": "",
        "apellidos": None,
        "numero_documento": "",
    }
    leido = client.get("/v1/cliente/perfil", headers=headers)
    assert leido.status_code == 200
    assert leido.json()["nombre"] == ""
    assert leido.json()["apellidos"] == ""

    doble.respuestas["actualizar_perfil"] = {
        "usuario_id": UID,
        "email": "camila@correo.com",
        "nombre": "Ana",
        "apellidos": "Lopez",
        "numero_documento": "1",
    }
    guardado = client.patch(
        "/v1/cliente/perfil", headers=headers, json={"nombre": "Ana", "apellidos": "Lopez"}
    )
    assert guardado.status_code == 200
    assert guardado.json()["nombre"] == "Ana"
    assert client.get("/cliente/perfil", headers=headers).status_code == 404
    assert (
        client.patch(
            "/cliente/perfil", headers=headers, json={"nombre": "Ana", "apellidos": "Lopez"}
        ).status_code
        == 404
    )


def test_aviso_v1_reenvia_multipart_y_el_detalle(client, doble):
    headers = {**_auth(client), "Idempotency-Key": "aviso-lugar-01"}
    respuesta = client.post(
        "/v1/cliente/siniestros",
        headers=headers,
        data={
            "poliza": "POL-88219-CO",
            "fechaHecho": "2026-03-12",
            "descripcion": "Choque",
            "lugar": "Calle 72",
            "geo": '{"lat": 4.65, "lng": -74.08, "precisionM": 12}',
        },
        files=[("archivos", ("dano.png", b"png", "image/png"))],
    )
    assert respuesta.status_code == 200, respuesta.text
    aviso = next(llamada for llamada in doble.llamadas if llamada["metodo"] == "registrar_aviso")
    assert aviso["datos"]["canal"] == "movil"
    assert aviso["datos"]["lugar"] == "Calle 72"
    assert aviso["datos"]["geo"] == {"lat": 4.65, "lng": -74.08, "precision_m": 12}
    invalida = client.post(
        "/v1/cliente/siniestros",
        headers={**_auth(client), "Idempotency-Key": "aviso-geo-malo"},
        data={"poliza": "POL-1", "fechaHecho": "2026-03-12", "descripcion": "Choque", "geo": "{"},
        files=[("archivos", ("dano.png", b"png", "image/png"))],
    )
    assert invalida.status_code == 422
    assert aviso["datos"]["poliza"]["numero"] == "POL-88219-CO"
    assert aviso["archivos"] == 1
    sin_clave = client.post(
        "/v1/cliente/siniestros",
        headers=_auth(client),
        data={"poliza": "POL-1", "fechaHecho": "2026-03-12", "descripcion": "Choque"},
        files=[("archivos", ("dano.png", b"png", "image/png"))],
    )
    assert sin_clave.status_code == 422
    doble.respuestas["detalle_siniestro"] = {
        "siniestro": {
            "id": "interno",
            "numero": "SIN-9",
            "estado": "pagado",
            "tipo": "asistido",
            "descripcion": "Choque",
            "lugar": "Calle 72",
            "poliza_numero": "POL-1",
            "historial": [{"estado": "recibido", "ocurrido_en": "2026-03-12"}],
        },
        "adjuntos": [{"nombre": "dano.png", "tipo": "foto", "content_type": "image/png", "url": "memoria://dano"}],
    }
    detalle = client.get("/v1/cliente/siniestros/interno", headers=_auth(client))
    assert detalle.status_code == 200
    assert detalle.json()["siniestroId"] == "SIN-9"
    assert detalle.json()["lugar"] == "Calle 72"
    assert detalle.json()["evidencia"][0]["nombre"] == "dano.png"
    assert detalle.json()["umbral"] is None
    assert detalle.json()["historial"] == [
        {"estado": "recibido", "fecha": "2026-03-12", "estadoTexto": "Recibido"}
    ]

    doble.respuestas["detalle_siniestro"] = {
        "siniestro": {
            "id": "interno",
            "numero": "SIN-9",
            "estado": "decidido",
            "resultado": "rechazado",
            "tipo": "asistido",
            "ramo": "soat-motocicleta",
            "descripcion": "Choque",
            "poliza_numero": "POL-1",
            "reserva": "350000.00",
            "geo": {"lat": "4.65", "lng": "-74.08", "precision_m": "12.00"},
            "umbral_automatico": "500000.00",
            "historial": [{"estado": "decidido", "ocurrido_en": "2026-03-13T10:00:00"}],
        },
        "decisiones": [
            {"resultado": "aprobado", "motivo": "primero"},
            {"resultado": "rechazado", "motivo": "Póliza no vigente en la fecha del hecho"},
        ],
        "adjuntos": [],
        "pago": {
            "clave_idempotencia": "clave",
            "comprobante": "CMP-1",
            "monto": "350000.00",
            "origen": "automatico",
            "autorizado_por": "sistema",
            "pagado_en": "2026-03-13T12:00:00",
        },
    }
    rechazo = client.get("/v1/cliente/siniestros/interno", headers=_auth(client)).json()
    assert rechazo["ramo"] == "SOAT motocicleta"
    assert rechazo["resultado"] == "rechazado"
    assert rechazo["motivo"] == "Póliza no vigente en la fecha del hecho"
    assert rechazo["reserva"] == 350000.0
    assert rechazo["geo"] == {"lat": 4.65, "lng": -74.08, "precisionM": 12}
    assert rechazo["pago"] == {
        "comprobante": "CMP-1",
        "monto": 350000.0,
        "moneda": "COP",
        "fecha": "2026-03-13T12:00:00",
    }
    assert "clave_idempotencia" not in rechazo["pago"]
    assert rechazo["umbral"] is None

    parametrico = {
        "siniestro": {
            "id": "interno",
            "numero": "SIN-9",
            "estado": "pagado",
            "resultado": "aprobado",
            "tipo": "parametrico",
            "ramo": "clima-y-vuelos",
            "umbral_automatico": "500000.00",
            "historial": [],
        },
        "decisiones": [],
        "adjuntos": [],
    }
    doble.respuestas["detalle_siniestro"] = parametrico
    pago_auto = client.get("/v1/cliente/siniestros/interno", headers=_auth(client)).json()
    assert pago_auto["umbral"] == "500000.00"
    assert pago_auto["estadoTexto"] == "Pagado"


def test_siniestros_v0_es_muestra_y_v1_traduce_la_lista(client, doble):
    headers = _auth(client)
    muestra = client.get("/cliente/siniestros", headers=headers).json()
    assert muestra["siniestros"][0]["siniestroId"] == "SIN-441"

    doble.respuestas["listar_siniestros"] = {"no": "lista"}
    assert client.get("/v1/cliente/siniestros", headers=headers).status_code == 502

    doble.respuestas["listar_siniestros"] = [
        {"id": "SIN-9", "estado": "recibido", "poliza": "POL-1", "evento_id": "evt"}
    ]
    cuerpo = client.get("/v1/cliente/siniestros", headers=headers).json()
    assert cuerpo["siniestros"][0]["siniestroId"] == "SIN-9"
    assert cuerpo["siniestros"][0]["ramo"] == "Sin clasificar"
    assert cuerpo["siniestros"][0]["poliza"] == "POL-1"


def test_avisos_v0_es_la_muestra_fija_sin_llamar_al_nucleo(client, doble):
    headers = _auth(client)
    cuerpo = client.get("/cliente/avisos", headers=headers).json()
    assert cuerpo["avisos"][0]["poliza"] == "POL-88219-CO"
    assert doble.llamadas == []


def test_avisos_v1_traduce_las_polizas_por_vencer_del_nucleo(client, doble):
    headers = _auth(client)
    doble.respuestas["polizas_por_vencer"] = [
        {"numero": "POL-77", "fin_vigencia": "2027-02-01", "estado": "vigente"}
    ]
    cuerpo = client.get("/v1/cliente/avisos", headers=headers).json()
    assert cuerpo == {"avisos": [{"tipo": "vencimiento", "poliza": "POL-77", "venceEn": "2027-02-01"}]}
    assert _nombres(doble) == ["polizas_por_vencer"]


def test_avisos_v1_sin_pendientes_devuelve_lista_vacia(client, doble):
    headers = _auth(client)
    assert client.get("/v1/cliente/avisos", headers=headers).json() == {"avisos": []}


def test_avisos_v1_respuesta_no_lista_es_502(client, doble):
    headers = _auth(client)
    doble.respuestas["polizas_por_vencer"] = {"no": "lista"}
    assert client.get("/v1/cliente/avisos", headers=headers).status_code == 502


def test_avisos_v1_poliza_incompleta_es_502(client, doble):
    headers = _auth(client)
    doble.respuestas["polizas_por_vencer"] = [{"numero": "POL-77"}]
    assert client.get("/v1/cliente/avisos", headers=headers).status_code == 502


def test_avisos_token_v0_no_llama_al_nucleo(client, doble):
    headers = _auth(client)
    respuesta = client.post(
        "/cliente/avisos/token", headers=headers, json={"token": "fcm-1", "plataforma": "android"}
    )
    assert respuesta.json() == {"estado": "aceptada", "plataforma": "android"}
    assert doble.llamadas == []


def test_avisos_token_v1_registra_el_dispositivo_en_notificaciones(client, doble):
    headers = _auth(client)
    respuesta = client.post(
        "/v1/cliente/avisos/token", headers=headers, json={"token": "fcm-1", "plataforma": "android"}
    )
    assert respuesta.json() == {"estado": "aceptada", "plataforma": "android"}
    assert _nombres(doble) == ["registrar_dispositivo"]
    assert doble.llamadas[0]["plataforma"] == "android"
    assert doble.llamadas[0]["token"] == "fcm-1"
