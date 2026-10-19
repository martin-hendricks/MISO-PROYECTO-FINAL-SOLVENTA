import httpx

from .conftest import EJEMPLO


def test_payload_de_vista_en_camelcase_y_recortado(client):
    respuesta = client.get(f"/v1/ejemplos/{EJEMPLO['id']}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["creadoEn"] == EJEMPLO["creado_en"]
    assert cuerpo["moneda"] == "COP"
    assert "creado_en" not in cuerpo
    assert "campoInternoDelNucleo" not in cuerpo and "campo_interno_del_nucleo" not in cuerpo


def test_registrar_reenvia_idempotency_key_y_correlacion(client, nucleo):
    respuesta = client.post(
        "/v1/ejemplos",
        json={"referencia": "REF-1", "monto": "100.00", "campoQueElBffNoConoce": 1},
        headers={"Idempotency-Key": "aviso-local-0001"},
    )

    assert respuesta.status_code == 201
    enviada = nucleo.peticiones[-1]
    assert enviada.headers["Idempotency-Key"] == "aviso-local-0001"
    assert enviada.headers["X-Correlation-Id"] == "corr-test"


def test_reintento_idempotente_devuelve_200(client, nucleo):
    nucleo.respuestas[("POST", "/v1/ejemplos")] = lambda _: httpx.Response(200, json=EJEMPLO)

    respuesta = client.post(
        "/v1/ejemplos",
        json={"referencia": "REF-1", "monto": "100.00"},
        headers={"Idempotency-Key": "aviso-local-0001"},
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["id"] == EJEMPLO["id"]


def test_registrar_sin_idempotency_key_es_422(client, nucleo):
    respuesta = client.post("/v1/ejemplos", json={"referencia": "R", "monto": "1"})

    assert respuesta.status_code == 422
    assert nucleo.peticiones == []


def test_rechazo_de_negocio_del_nucleo_se_propaga(client, nucleo):
    nucleo.respuestas[("POST", "/v1/ejemplos")] = lambda _: httpx.Response(
        422, json={"codigo": "monto_fuera_de_rango", "mensaje": "Monto fuera de rango"}
    )

    respuesta = client.post(
        "/v1/ejemplos",
        json={"referencia": "R", "monto": "1"},
        headers={"Idempotency-Key": "clave-0001"},
    )

    assert respuesta.status_code == 422
    assert respuesta.json() == {"codigo": "monto_fuera_de_rango", "mensaje": "Monto fuera de rango"}


def test_inexistente_es_404(client):
    assert client.get("/v1/ejemplos/no-existe").status_code == 404


def test_nucleo_caido_se_enmascara_como_503(client, nucleo):
    def caido(request):
        raise httpx.ConnectError("conexión rechazada", request=request)

    nucleo.respuestas[("GET", f"/v1/ejemplos/{EJEMPLO['id']}")] = caido
    respuesta = client.get(f"/v1/ejemplos/{EJEMPLO['id']}")

    assert respuesta.status_code == 503
    assert "ms-ejemplo" not in respuesta.text


def test_error_500_del_nucleo_tambien_es_503(client, nucleo):
    nucleo.respuestas[("GET", f"/v1/ejemplos/{EJEMPLO['id']}")] = lambda _: httpx.Response(500, text="Traceback")
    assert client.get(f"/v1/ejemplos/{EJEMPLO['id']}").status_code == 503


def test_inicio_compone_las_dos_fuentes(client):
    respuesta = client.get("/v1/inicio")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [e["id"] for e in cuerpo["ejemplos"]] == [EJEMPLO["id"]]
    assert cuerpo["indicadores"] == {"total": 1, "montoTotal": "100.00"}
    assert cuerpo["degradado"] == []


def test_inicio_degrada_si_cae_la_fuente_opcional(client, nucleo):
    nucleo.respuestas[("GET", "/v1/ejemplos/indicadores")] = lambda _: httpx.Response(503)

    cuerpo = client.get("/v1/inicio").json()

    assert cuerpo["indicadores"] is None
    assert cuerpo["degradado"] == ["indicadores"]
    assert len(cuerpo["ejemplos"]) == 1


def test_inicio_falla_si_cae_la_fuente_principal(client, nucleo):
    nucleo.respuestas[("GET", "/v1/ejemplos")] = lambda _: httpx.Response(503)
    assert client.get("/v1/inicio").status_code == 503
