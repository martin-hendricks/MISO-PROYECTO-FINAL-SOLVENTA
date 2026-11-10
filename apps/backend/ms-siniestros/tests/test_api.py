from decimal import Decimal
from uuid import uuid4

from .conftest import cabecera


def _ingerir(client, evento_id="evt-1", **extra):
    cuerpo = {
        "evento_id": evento_id,
        "valor": "100.00",
        "umbral": "80.00",
        "poliza_vigente": True,
        "monto_pago": "500.00",
        **extra,
    }
    return client.post("/v1/eventos-parametricos", json=cuerpo)


def test_ingerir_evento_201_umbral_cumplido_queda_pagado(client):
    respuesta = _ingerir(client)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["siniestro"]["estado"] == "pagado"
    assert cuerpo["evaluacion"]["decision"] is True
    assert cuerpo["pago"]["monto"] == "500.00"
    assert cuerpo["procesado"] is True


def test_ingerir_evento_umbral_no_cumplido_no_paga(client):
    respuesta = _ingerir(client, valor="10.00")

    cuerpo = respuesta.json()
    assert cuerpo["siniestro"]["estado"] == "decidido"
    assert cuerpo["evaluacion"]["decision"] is False
    assert cuerpo["pago"] is None


def test_reingesta_del_mismo_evento_devuelve_200_y_no_duplica(client):
    primero = _ingerir(client, evento_id="evt-dup")
    segundo = _ingerir(client, evento_id="evt-dup")

    assert primero.status_code == 201
    assert segundo.status_code == 200
    assert segundo.json()["siniestro"]["id"] == primero.json()["siniestro"]["id"]
    assert segundo.json()["pago"]["pagado_en"] == primero.json()["pago"]["pagado_en"]
    assert segundo.json()["pago"]["monto"] == primero.json()["pago"]["monto"]
    assert segundo.json()["pago"]["comprobante"] == primero.json()["pago"]["comprobante"]
    assert primero.json()["pago"]["comprobante"].startswith("CMP-")
    assert segundo.json()["procesado"] is False


def test_evento_sin_id_es_422(client):
    respuesta = client.post(
        "/v1/eventos-parametricos",
        json={"evento_id": "", "valor": "1", "umbral": "1", "poliza_vigente": True, "monto_pago": "1"},
    )
    assert respuesta.status_code == 422


def test_poliza_no_vigente_no_paga(client):
    respuesta = _ingerir(client, evento_id="evt-no-vigente", valor="999", poliza_vigente=False)

    cuerpo = respuesta.json()
    assert cuerpo["evaluacion"]["motivo"] == "poliza_no_vigente"
    assert cuerpo["pago"] is None


def test_consultar_siniestro(client):
    creado = _ingerir(client, evento_id="evt-consulta").json()

    respuesta = client.get(f"/v1/siniestros/{creado['siniestro']['id']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "pagado"
    assert len(respuesta.json()["historial"]) == 5


def test_consultar_siniestro_inexistente_es_404(client):
    respuesta = client.get(f"/v1/siniestros/{uuid4()}")
    assert respuesta.status_code == 404
    assert respuesta.json()["codigo"] == "no_encontrado"


def test_listar_siniestros(client):
    _ingerir(client, evento_id="evt-list-1")
    _ingerir(client, evento_id="evt-list-2")

    respuesta = client.get("/v1/siniestros?limite=5")

    assert respuesta.status_code == 200
    assert len(respuesta.json()) == 2


def test_cambiar_estado_invalido_es_409(client):
    creado = _ingerir(client, evento_id="evt-409", valor="10").json()  # queda en 'decidido'
    siniestro_id = creado["siniestro"]["id"]

    respuesta = client.post(
        f"/v1/siniestros/{siniestro_id}/estado", json={"estado": "recibido", "origen": "operador-1"}
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["codigo"] == "transicion_invalida"


def test_cambiar_estado_valido_200(client):
    creado = _ingerir(client, evento_id="evt-200", valor="10").json()  # queda en 'decidido'
    siniestro_id = creado["siniestro"]["id"]

    respuesta = client.post(
        f"/v1/siniestros/{siniestro_id}/estado", json={"estado": "enrutado", "origen": "operador-2"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "enrutado"
    assert respuesta.json()["historial"][-1]["origen"] == "operador-2"


def test_cambiar_estado_siniestro_inexistente_es_404(client):
    respuesta = client.post(
        f"/v1/siniestros/{uuid4()}/estado", json={"estado": "en_evaluacion", "origen": "operador"}
    )
    assert respuesta.status_code == 404


def test_health_live_metrics_y_correlacion(client):
    salud = client.get("/health/live", headers={"X-Correlation-Id": "c-123"})

    assert salud.json() == {"status": "ok"}
    assert salud.headers["X-Correlation-Id"] == "c-123"
    assert "http_request_duration_seconds" in client.get("/metrics").text


def test_health_ready_sin_base_de_datos_devuelve_503(client):
    # El cliente de pruebas crea la app real (lifespan real -> motor SQLAlchemy real)
    # pero sin un Postgres escuchando en DATABASE_URL: el ping debe fallar controladamente.
    respuesta = client.get("/health/ready")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "unavailable"}


# --- HU-61 (back-office): siniestros abiertos de una póliza ------------------------


def test_ingerir_con_poliza_id_lo_devuelve_en_el_siniestro(client):
    poliza_id = str(uuid4())

    respuesta = _ingerir(client, evento_id="evt-con-poliza", poliza_id=poliza_id)

    assert respuesta.json()["siniestro"]["poliza_id"] == poliza_id


def test_ingerir_sin_poliza_id_lo_devuelve_null(client):
    respuesta = _ingerir(client, evento_id="evt-sin-poliza")

    assert respuesta.json()["siniestro"]["poliza_id"] is None


def test_siniestros_abiertos_excluye_pagados_e_incluye_solo_la_poliza_pedida(client):
    poliza_id = str(uuid4())
    # umbral cumplido -> PAGADO (no cuenta como abierto)
    _ingerir(client, evento_id="evt-abiertos-pagado", valor="100", poliza_id=poliza_id)
    # umbral no cumplido -> DECIDIDO (cuenta como abierto)
    _ingerir(client, evento_id="evt-abiertos-decidido", valor="10", poliza_id=poliza_id)
    # otra póliza, no debe aparecer
    _ingerir(client, evento_id="evt-abiertos-otra", valor="10", poliza_id=str(uuid4()))

    respuesta = client.get("/v1/siniestros/abiertos", params={"poliza_id": poliza_id})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["abiertos"] == 1
    assert [s["evento_id"] for s in cuerpo["siniestros"]] == ["evt-abiertos-decidido"]


def test_siniestros_abiertos_sin_siniestros_devuelve_cero(client):
    respuesta = client.get("/v1/siniestros/abiertos", params={"poliza_id": str(uuid4())})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"abiertos": 0, "siniestros": []}


def test_siniestros_abiertos_requiere_poliza_id(client):
    respuesta = client.get("/v1/siniestros/abiertos")

    assert respuesta.status_code == 422


def test_pagos_recibidos_respeta_rol_y_dueno(client):
    dueno = uuid4()
    creado = _ingerir(
        client,
        evento_id="evt-billetera-api",
        monto_pago="180000.00",
        usuario_id=str(dueno),
        ramo="clima-vuelos",
        poliza_numero="POL-11002-CO",
        descripcion="retraso de vuelo",
    ).json()
    siniestro_id = creado["siniestro"]["id"]

    como_dueno = client.get("/v1/pagos-recibidos", headers=cabecera("cliente", dueno))
    assert como_dueno.status_code == 200
    cuerpo = como_dueno.json()
    assert cuerpo["moneda"] == "COP"
    assert Decimal(cuerpo["total"]) == Decimal("180000.00")
    assert cuerpo["pagos"][0]["siniestro_id"] == siniestro_id
    assert cuerpo["pagos"][0]["tipo"] == "parametrico"
    assert cuerpo["pagos"][0]["ramo"] == "clima-vuelos"

    ajeno = client.get(
        "/v1/pagos-recibidos", params={"usuario_id": str(uuid4())}, headers=cabecera("cliente", dueno)
    )
    assert ajeno.status_code == 404
    assert client.get(f"/v1/pagos-recibidos/{siniestro_id}", headers=cabecera("cliente", uuid4())).status_code == 404
    assert client.get("/v1/pagos-recibidos", headers=cabecera("operador")).status_code == 422
    assert client.get("/v1/pagos-recibidos", headers=cabecera("asesor")).status_code == 422
    assert client.get("/v1/pagos-recibidos", headers={"Authorization": ""}).status_code == 401
    # Un rol fuera de cliente/asesor/operador se rechaza al validar el token.
    assert client.get("/v1/pagos-recibidos", headers=cabecera("admin")).status_code == 401
    assert _ingerir(client, evento_id="evt-largo", ramo="x" * 61).status_code == 422


def test_cliente_sin_pagos_recibe_total_cero(client):
    respuesta = client.get("/v1/pagos-recibidos", headers=cabecera("cliente", uuid4()))
    assert respuesta.status_code == 200
    assert respuesta.json()["pagos"] == []
    assert Decimal(respuesta.json()["total"]) == Decimal("0.00")
