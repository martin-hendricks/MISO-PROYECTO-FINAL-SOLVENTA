"""Siniestro asistido en bff-web (HU-157, HU-160): cliente y cola del operador."""

import json

import httpx

from tests.conftest import token

SID = "99999999-9999-4999-8999-999999999999"
POLIZA_ID = "77777777-7777-4777-8777-777777777777"
OFERTA_ID = "22222222-2222-4222-8222-222222222222"
# uid que el doble de ms-identidad pone en el JWT (tests/conftest.py): el dueño real.
DUENO = "11111111-1111-1111-1111-111111111111"

POLIZA = {
    "id": POLIZA_ID,
    "numero": "POL-88421",
    "oferta_id": OFERTA_ID,
    "usuario_id": DUENO,
    "inicio_vigencia": "2026-09-01",
    "fin_vigencia": "2027-09-01",
    "estado": "VIGENTE",  # así responde ms-polizas
    "coberturas": [{"nombre": "dano", "suma_asegurada": "89000", "deducible": "0"}],
    "prima": {"valor": "89000", "periodicidad": "ANUAL"},
    "renovable": False,
}

SINIESTRO = {
    "id": SID,
    "numero": "SIN-1001",
    "tipo": "asistido",
    "estado": "en_evaluacion",
    "creado_en": "2026-11-02T10:00:00Z",
    "historial": [
        {"estado": "recibido", "ocurrido_en": "2026-11-02T10:00:00Z", "origen": "cliente:web"},
        {"estado": "en_evaluacion", "ocurrido_en": "2026-11-02T10:00:02Z", "origen": "motor"},
    ],
    "usuario_id": DUENO,
    "poliza_numero": "POL-88421",
    "ramo": "vida-crediticia",
    "fecha_hecho": "2026-11-01",
    "descripcion": "Fallecimiento del asegurado",
    "geo": None,
    "reserva": "3200000.00",
    "umbral_automatico": "500000.00",
    "resultado": None,
    "requiere_revision": True,
    "motivo_revision": "La reserva supera el umbral de aprobación automática",
}

ADJUNTO = {
    "id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    "tipo": "documento",
    "nombre": "certificado.pdf",
    "content_type": "application/pdf",
    "tamano_bytes": 10,
    "sha256": "x" * 64,
    "cargado_en": "2026-11-02T10:00:00Z",
    "url": "http://localhost:4566/firmada",
    "url_expira_segundos": 300,
}


def detalle(siniestro=None, **extra):
    return {
        "siniestro": siniestro or SINIESTRO,
        "adjuntos": [ADJUNTO],
        "decisiones": [],
        "pago": None,
        "intentos_pago": [],
    } | extra


def auth(client, rol):
    return {"Authorization": f"Bearer {token(client, rol)}"}


# ---------------------------------------------------------------- cliente


def _preparar_alta(nucleo_polizas, nucleo_cotizacion, nucleo_siniestros, poliza=POLIZA):
    nucleo_polizas.respuestas[("GET", "/v1/polizas/numero/POL-88421")] = lambda _: httpx.Response(200, json=poliza)
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/por-oferta/{OFERTA_ID}")] = lambda _: httpx.Response(
        200, json={"producto": "proteccion-dispositivo", "prima": "89000", "moneda": "COP"}
    )
    recibido = {**SINIESTRO, "estado": "recibido", "requiere_revision": False}
    nucleo_siniestros.respuestas[("POST", "/v1/siniestros")] = lambda _: httpx.Response(201, json=detalle(recibido))


def _reportar(client, geo='{"lat": 4.65, "lng": -74.08, "precisionM": 12}', cabeceras=None):
    datos = {"poliza": "POL-88421", "fechaHecho": "2026-11-01", "descripcion": "Pantalla rota"}
    if geo is not None:
        datos["geo"] = geo
    return client.post(
        "/v1/cliente/siniestros",
        headers=auth(client, "cliente") | (cabeceras or {}),
        data=datos,
        files=[("archivos", ("dano.png", b"\x89PNG", "image/png"))],
    )


def test_reportar_envia_foto_de_poliza_y_evidencia_al_nucleo(client, nucleo_polizas, nucleo_cotizacion, nucleo_siniestros):
    _preparar_alta(nucleo_polizas, nucleo_cotizacion, nucleo_siniestros)

    r = _reportar(client, cabeceras={"Idempotency-Key": "k-1"})

    assert r.status_code == 201, r.text
    assert r.json() == {"id": SID, "siniestroId": "SIN-1001", "estado": "recibido"}
    enviado = nucleo_siniestros.peticiones[-1]
    assert enviado.headers["Idempotency-Key"] == "k-1"
    cuerpo = enviado.read()
    assert b'name="archivos"; filename="dano.png"' in cuerpo
    datos = json.loads(cuerpo.split(b'name="datos"\r\n\r\n')[1].split(b"\r\n--")[0])
    assert datos["usuario_id"] == DUENO
    assert datos["canal"] == "web"
    assert datos["poliza"]["ramo"] == "proteccion-dispositivo"
    assert datos["poliza"]["poliza_id"] == POLIZA_ID
    assert datos["poliza"]["estado"] == "vigente"
    assert "suma_asegurada" not in datos["poliza"]
    assert datos["geo"] == {"lat": 4.65, "lng": -74.08, "precision_m": 12.0}
    assert datos["tipos_adjuntos"] == ["foto"]


def test_reportar_sin_ubicacion_sigue(client, nucleo_polizas, nucleo_cotizacion, nucleo_siniestros):
    _preparar_alta(nucleo_polizas, nucleo_cotizacion, nucleo_siniestros)
    assert _reportar(client, geo=None).status_code == 201
    cuerpo = nucleo_siniestros.peticiones[-1].read()
    assert b'"geo": null' in cuerpo


def test_reportar_sobre_poliza_ajena_es_404(client, nucleo_polizas, nucleo_cotizacion, nucleo_siniestros):
    _preparar_alta(nucleo_polizas, nucleo_cotizacion, nucleo_siniestros, poliza={**POLIZA, "usuario_id": SID})
    assert _reportar(client).status_code == 404
    assert not any(p.url.path == "/v1/siniestros" for p in nucleo_siniestros.peticiones)


def test_reportar_ubicacion_invalida_es_400(client, nucleo_polizas, nucleo_cotizacion, nucleo_siniestros):
    _preparar_alta(nucleo_polizas, nucleo_cotizacion, nucleo_siniestros)
    assert _reportar(client, geo='{"lat": 200, "lng": 0}').status_code == 400


def test_reportar_evidencia_rechazada_por_el_nucleo_es_422(client, nucleo_polizas, nucleo_cotizacion, nucleo_siniestros):
    _preparar_alta(nucleo_polizas, nucleo_cotizacion, nucleo_siniestros)
    nucleo_siniestros.respuestas[("POST", "/v1/siniestros")] = lambda _: httpx.Response(
        422, json={"codigo": "evidencia_tipo_no_permitido", "mensaje": "La evidencia debe ser PNG, JPG, PDF o MP4"}
    )
    r = _reportar(client)
    assert r.status_code == 422
    assert r.json()["codigo"] == "evidencia_tipo_no_permitido"


def test_mis_siniestros_filtra_por_el_usuario_de_la_sesion(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", "/v1/siniestros")] = lambda _: httpx.Response(200, json=[SINIESTRO])

    r = client.get("/v1/cliente/siniestros", headers=auth(client, "cliente"))

    assert r.status_code == 200
    fila = r.json()["siniestros"][0]
    assert fila["siniestroId"] == "SIN-1001"
    assert fila["ramo"] == "Vida crediticia"  # nombre canónico (app/ramos.py), no el código
    assert fila["estado"] == "en_evaluacion"
    assert fila["reserva"] == 3200000.0
    assert nucleo_siniestros.peticiones[-1].url.params["usuario_id"] == DUENO


def test_detalle_del_cliente_muestra_motivo_de_rechazo_sin_reglas_internas(client, nucleo_siniestros):
    rechazado = {**SINIESTRO, "estado": "decidido", "resultado": "rechazado", "requiere_revision": False}
    decision = {
        "origen": "operador",
        "actor": "ana@solventa.com",
        "resultado": "rechazado",
        "motivo": "Falta soporte",
        "reglas": [],
        "decidida_en": "2026-11-02T11:00:00Z",
    }
    nucleo_siniestros.respuestas[("GET", f"/v1/siniestros/{SID}/detalle")] = lambda _: httpx.Response(
        200, json=detalle(rechazado, decisiones=[decision])
    )

    r = client.get(f"/v1/cliente/siniestros/{SID}", headers=auth(client, "cliente"))

    body = r.json()
    assert body["motivo"] == "Falta soporte"
    assert body["evidencia"][0]["url"] == ADJUNTO["url"]
    assert "decisiones" not in body and "ana@solventa.com" not in r.text
    assert nucleo_siniestros.peticiones[-1].url.params["usuario_id"] == DUENO


def test_operador_no_usa_rutas_del_cliente(client):
    assert client.get("/v1/cliente/siniestros", headers=auth(client, "operador")).status_code == 403


# --------------------------------------------------------------- operador


def test_cola_cuenta_por_chip_y_ordena_por_antiguedad(client, nucleo_siniestros):
    viejo = {**SINIESTRO, "id": "11111111-1111-4111-8111-111111111111", "creado_en": "2026-11-01T08:00:00Z"}

    def responder(request):
        params = request.url.params
        if params.get("requiere_revision") == "true":
            return httpx.Response(200, json=[SINIESTRO, viejo])
        if params.get("resultado") == "aprobado":
            return httpx.Response(200, json=[])
        if params.get("resultado") == "rechazado":
            return httpx.Response(200, json=[])
        return httpx.Response(200, json=[SINIESTRO, viejo])

    nucleo_siniestros.respuestas[("GET", "/v1/siniestros")] = responder

    body = client.get("/v1/operador/avisos", headers=auth(client, "operador")).json()

    assert body["conteos"] == {"pendientes": 2, "aprobados": 0, "rechazados": 0, "todos": 2}
    assert [a["id"] for a in body["avisos"]] == [viejo["id"], SID]
    assert body["avisos"][0]["estadoCola"] == "en_revision"
    assert body["avisos"][0]["poliza"] == "POL-88421"
    assert all(p.url.params["tipo"] == "asistido" for p in nucleo_siniestros.peticiones)


def test_cola_con_filtro_invalido_es_422(client):
    assert client.get("/v1/operador/avisos?filtro=otro", headers=auth(client, "operador")).status_code == 422


def test_caso_del_operador_trae_evidencia_y_monto(client, nucleo_siniestros):
    nucleo_siniestros.respuestas[("GET", f"/v1/siniestros/{SID}/detalle")] = lambda _: httpx.Response(
        200, json=detalle()
    )
    body = client.get(f"/v1/operador/avisos/{SID}", headers=auth(client, "operador")).json()
    assert body["montoEstimado"] == 3200000.0
    assert body["bajoMonto"] is False
    assert body["evidencia"][0]["nombre"] == "certificado.pdf"
    assert body["motivoRevision"].startswith("La reserva")


def test_rechazo_envia_motivo_y_actor(client, nucleo_siniestros):
    rechazado = {**SINIESTRO, "estado": "decidido", "resultado": "rechazado", "requiere_revision": False}
    nucleo_siniestros.respuestas[("POST", f"/v1/siniestros/{SID}/decision")] = lambda _: httpx.Response(
        200, json=detalle(rechazado)
    )
    r = client.post(
        "/v1/operador/avisos/decision",
        headers=auth(client, "operador"),
        json={"siniestroId": SID, "decision": "rechazar", "motivo": "Falta soporte"},
    )
    assert r.status_code == 200
    assert r.json()["estadoCola"] == "rechazado"
    peticion = nucleo_siniestros.peticiones[-1]
    enviado = json.loads(peticion.read())
    assert enviado == {"resultado": "rechazado", "motivo": "Falta soporte", "actor": "operador@solventa.com"}
    # El token de la sesión viaja al núcleo: ms-siniestros vuelve a exigir el rol operador.
    assert peticion.headers["Authorization"].startswith("Bearer ")


def test_perito_y_pago(client, nucleo_siniestros):
    enrutado = {**SINIESTRO, "estado": "enrutado", "requiere_revision": False}
    nucleo_siniestros.respuestas[("POST", f"/v1/siniestros/{SID}/perito")] = lambda _: httpx.Response(
        200, json=detalle(enrutado)
    )
    assert client.post(
        f"/v1/operador/avisos/{SID}/perito", headers=auth(client, "operador"), json={"motivo": "Inspección"}
    ).json()["estadoCola"] == "enrutado"

    pagado = {**SINIESTRO, "estado": "pagado", "resultado": "aprobado", "requiere_revision": False}
    pago = {"clave_idempotencia": "idem-1", "comprobante": "CMP-1", "monto": "420000.00", "origen": "operador",
            "autorizado_por": "persona@solventa.com", "pagado_en": "2026-11-02T12:00:00Z"}
    nucleo_siniestros.respuestas[("POST", f"/v1/siniestros/{SID}/pago")] = lambda _: httpx.Response(
        200, json={"pago": pago, "reintento": True, "detalle": detalle(pagado, pago=pago)}
    )
    r = client.post(f"/v1/operador/avisos/{SID}/pago", headers=auth(client, "operador"))
    assert r.status_code == 200
    assert r.json()["reintento"] is True
    assert r.json()["pago"]["comprobante"] == "CMP-1"
    assert r.json()["caso"]["estadoCola"] == "pagado"


def test_cliente_no_entra_a_la_cola(client):
    assert client.get("/v1/operador/avisos", headers=auth(client, "cliente")).status_code == 403
