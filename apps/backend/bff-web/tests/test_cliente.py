import httpx

from tests.conftest import token

COTIZACION_ID = "11111111-1111-1111-1111-111111111111"
OFERTA_ID = "22222222-2222-2222-2222-222222222222"
PAGO_ID = "33333333-3333-3333-3333-333333333333"

COTIZACION_SALIDA = {
    "cotizacion_id": COTIZACION_ID,
    "estado": "oferta_vigente",
    "producto": "proteccion-dispositivo",
    "creada_en": "2026-10-01T00:00:00Z",
    "prima": "89000.00",
    "prima_neta": "80000.00",
    "gastos_expedicion": "9000.00",
    "moneda": "COP",
    "vence_en": "2026-11-01T00:00:00Z",
    "factor_riesgo_origen": "stub",
    "vencida": False,
}

ACEPTACION_SALIDA = {
    "cotizacion_id": COTIZACION_ID,
    "oferta_id": OFERTA_ID,
    "estado": "aceptada",
    "prima": "89000.00",
    "moneda": "COP",
    "aceptada_en": "2026-10-01T00:00:00Z",
    "suscripcion_id": "44444444-4444-4444-4444-444444444444",
    # Valores reales del enum Decision de ms-suscripcion (ver
    # apps/backend/ms-suscripcion/app/domain/modelos.py): ACEPTADA/RECHAZADA.
    "decision": "ACEPTADA",
    "motivo": "riesgo_aceptable",
}

ACEPTACION_RECHAZADA = {**ACEPTACION_SALIDA, "decision": "RECHAZADA", "motivo": "score_fuera_de_apetito"}

PAGO_SALIDA = {
    "id": PAGO_ID,
    "oferta_id": OFERTA_ID,
    "monto": "89000.00",
    "estado": "confirmado",
    "idempotency_key": "clave",
    "referencia_externa": "ref-1",
    "fecha": "2026-10-01T00:00:00Z",
}

POLIZA_SALIDA = {
    "id": "55555555-5555-5555-5555-555555555555",
    "numero": "POL-88219-CO",
    "oferta_id": OFERTA_ID,
    "usuario_id": "66666666-6666-6666-6666-666666666666",
    "inicio_vigencia": "2026-10-01T00:00:00Z",
    "fin_vigencia": "2027-10-01T00:00:00Z",
    "estado": "vigente",
    "coberturas": [{"nombre": "cobertura-base", "suma_asegurada": "89000.00", "deducible": "0"}],
}


def _auth(client, rol="cliente"):
    return {"Authorization": f"Bearer {token(client, rol)}"}


def test_cotizacion_y_reconsulta(client, nucleo_cotizacion):
    nucleo_cotizacion.respuestas[("POST", "/v1/cotizaciones")] = lambda _: httpx.Response(
        201, json=COTIZACION_SALIDA
    )
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/{COTIZACION_ID}")] = lambda _: httpx.Response(
        200, json=COTIZACION_SALIDA
    )

    headers = _auth(client)
    created = client.post(
        "/v1/cliente/cotizaciones",
        headers=headers,
        json={"ramo": "Protección de dispositivo", "datosRiesgo": {"valorDispositivo": 2400000}},
    )
    assert created.status_code == 200
    offer = created.json()
    assert offer["cotizacionId"] == COTIZACION_ID
    assert offer["moneda"] == "COP"
    assert offer["ramo"] == "Protección de dispositivo"
    assert offer["primaNeta"] == "80000.00"
    assert offer["expedicion"] == "9000.00"

    peticion = nucleo_cotizacion.peticiones[-1]
    assert peticion.headers["Idempotency-Key"]
    cuerpo = peticion.read()
    import json as _json

    assert _json.loads(cuerpo)["producto"] == "proteccion-dispositivo"

    again = client.get(f"/v1/cliente/cotizaciones/{COTIZACION_ID}", headers=headers)
    assert again.status_code == 200
    assert again.json()["cotizacionId"] == COTIZACION_ID


def test_cliente_id_en_cotizacion_de_cliente_es_400(client):
    response = client.post(
        "/v1/cliente/cotizaciones",
        headers=_auth(client),
        json={"ramo": "x", "datosRiesgo": {}, "clienteId": "CLI-18"},
    )
    assert response.status_code == 400


def test_cotizacion_servicio_no_disponible_es_503(client, nucleo_cotizacion):
    def caido(request):
        raise httpx.ConnectError("conexión rechazada", request=request)

    nucleo_cotizacion.respuestas[("POST", "/v1/cotizaciones")] = caido

    response = client.post(
        "/v1/cliente/cotizaciones",
        headers=_auth(client),
        json={"ramo": "Protección de dispositivo", "datosRiesgo": {}},
    )
    assert response.status_code == 503
    assert "ms-cotizacion" not in response.text


def test_cotizacion_rechazo_de_negocio_se_propaga(client, nucleo_cotizacion):
    nucleo_cotizacion.respuestas[("POST", "/v1/cotizaciones")] = lambda _: httpx.Response(
        422, json={"codigo": "producto_suspendido", "mensaje": "Producto suspendido"}
    )

    response = client.post(
        "/v1/cliente/cotizaciones",
        headers=_auth(client),
        json={"ramo": "Protección de dispositivo", "datosRiesgo": {}},
    )
    assert response.status_code == 422
    assert response.json() == {"codigo": "producto_suspendido", "mensaje": "Producto suspendido"}


def test_emision_feliz_encadena_aceptacion_pago_y_poliza(client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas):
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_SALIDA
    )
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/{COTIZACION_ID}")] = lambda _: httpx.Response(
        200, json=COTIZACION_SALIDA
    )
    nucleo_pagos.respuestas[("POST", "/v1/pagos/primas")] = lambda _: httpx.Response(201, json=PAGO_SALIDA)
    nucleo_polizas.respuestas[("POST", "/v1/polizas")] = lambda _: httpx.Response(201, json=POLIZA_SALIDA)

    response = client.post(
        "/v1/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": COTIZACION_ID},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["resultado"] == "EMITIDA"
    assert body["poliza"]["numero"] == "POL-88219-CO"
    assert body["poliza"]["estado"] == "vigente"
    assert body["poliza"]["ramo"] == COTIZACION_SALIDA["producto"]
    assert body["poliza"]["producto"] == COTIZACION_SALIDA["producto"]
    assert body["poliza"]["inicioVigencia"] == POLIZA_SALIDA["inicio_vigencia"]
    assert body["poliza"]["finVigencia"] == POLIZA_SALIDA["fin_vigencia"]
    assert body["poliza"]["moneda"] == ACEPTACION_SALIDA["moneda"]
    assert body["poliza"]["primaTotal"] == float(ACEPTACION_SALIDA["prima"])

    pago_enviado = nucleo_pagos.peticiones[-1]
    assert pago_enviado is not None
    poliza_enviada = nucleo_polizas.peticiones[-1]
    import json as _json

    assert _json.loads(poliza_enviada.read())["token_pago_confirmado"] == PAGO_ID


def test_emision_cuando_decision_es_rechazada_no_cobra_ni_emite(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas
):
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_RECHAZADA
    )

    response = client.post(
        "/v1/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": COTIZACION_ID},
    )

    assert response.status_code == 200
    assert response.json() == {
        "resultado": "RECHAZADA",
        "motivo": {"codigo": ACEPTACION_RECHAZADA["motivo"], "mensaje": ACEPTACION_RECHAZADA["motivo"]},
    }
    assert nucleo_pagos.peticiones == []
    assert nucleo_polizas.peticiones == []


def test_emision_con_firma_fallida_responde_rechazo_con_motivo(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas
):
    fallida = {"codigo": "firma_no_exitosa", "mensaje": "La firma electrónica no fue exitosa: Firma rechazada"}
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_SALIDA
    )
    nucleo_pagos.respuestas[("POST", "/v1/pagos/primas")] = lambda _: httpx.Response(201, json=PAGO_SALIDA)
    nucleo_polizas.respuestas[("POST", "/v1/polizas")] = lambda _: httpx.Response(422, json=fallida)

    response = client.post(
        "/v1/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": COTIZACION_ID},
    )

    assert response.status_code == 200
    assert response.json() == {"resultado": "RECHAZADA", "motivo": fallida}


def test_emision_propaga_otros_rechazos_de_polizas(client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas):
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_SALIDA
    )
    nucleo_pagos.respuestas[("POST", "/v1/pagos/primas")] = lambda _: httpx.Response(201, json=PAGO_SALIDA)
    nucleo_polizas.respuestas[("POST", "/v1/polizas")] = lambda _: httpx.Response(
        422, json={"codigo": "sin_cobro_exitoso", "mensaje": "No hay cobro"}
    )

    response = client.post(
        "/v1/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": COTIZACION_ID},
    )

    assert response.status_code == 422


def test_emision_cuando_pago_falla_no_llama_a_polizas(client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas):
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_SALIDA
    )

    def pago_caido(request):
        raise httpx.ConnectError("conexión rechazada", request=request)

    nucleo_pagos.respuestas[("POST", "/v1/pagos/primas")] = pago_caido

    response = client.post(
        "/v1/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": COTIZACION_ID},
    )

    assert response.status_code == 503
    assert nucleo_polizas.peticiones == []


def test_emision_rechazo_de_aceptacion_se_propaga(client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas):
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        409, json={"codigo": "oferta_vencida", "mensaje": "La oferta ya venció"}
    )

    response = client.post(
        "/v1/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": COTIZACION_ID},
    )

    assert response.status_code == 409
    assert response.json() == {"codigo": "oferta_vencida", "mensaje": "La oferta ya venció"}
    assert nucleo_pagos.peticiones == []
    assert nucleo_polizas.peticiones == []


def test_billetera_devuelve_las_polizas_del_usuario(client, nucleo_polizas, nucleo_cotizacion):
    nucleo_polizas.respuestas[("GET", "/v1/polizas")] = lambda _: httpx.Response(
        200, json=[POLIZA_SALIDA]
    )
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/por-oferta/{OFERTA_ID}")] = lambda _: httpx.Response(
        200, json=COTIZACION_SALIDA
    )

    respuesta = client.get("/v1/cliente/polizas", headers=_auth(client))

    assert respuesta.status_code == 200
    polizas = respuesta.json()["polizas"]
    assert len(polizas) == 1
    assert polizas[0]["numero"] == "POL-88219-CO"
    assert polizas[0]["estado"] == "VIGENTE"
    assert polizas[0]["venceEn"] == "2027-10-01T00:00:00Z"
    assert polizas[0]["producto"] == COTIZACION_SALIDA["producto"]
    assert polizas[0]["inicioVigencia"] == POLIZA_SALIDA["inicio_vigencia"]
    assert polizas[0]["finVigencia"] == POLIZA_SALIDA["fin_vigencia"]
    assert polizas[0]["moneda"] == "COP"
    assert polizas[0]["primaTotal"] == 89000.0
    assert polizas[0]["ramo"] == COTIZACION_SALIDA["producto"]
    assert "cobertura-base" in polizas[0]["resumen"]

    peticion = nucleo_polizas.peticiones[-1]
    assert peticion.url.params["limite"] == "20"


def test_billetera_degrada_a_placeholder_si_ms_cotizacion_no_responde(client, nucleo_polizas, nucleo_cotizacion):
    """Si la reconsulta del producto falla (servicio caído o la cotización ya
    no existe), la póliza se devuelve igual con el placeholder de ramo: el
    dato de presentación no debe bloquear ver la póliza."""
    nucleo_polizas.respuestas[("GET", "/v1/polizas")] = lambda _: httpx.Response(
        200, json=[POLIZA_SALIDA]
    )
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/por-oferta/{OFERTA_ID}")] = lambda _: httpx.Response(
        503
    )

    respuesta = client.get("/v1/cliente/polizas", headers=_auth(client))

    assert respuesta.status_code == 200
    assert respuesta.json()["polizas"][0]["ramo"] == "Sin clasificar"


def test_billetera_servicio_no_disponible_es_503(client, nucleo_polizas):
    def caido(request):
        raise httpx.ConnectError("conexión rechazada", request=request)

    nucleo_polizas.respuestas[("GET", "/v1/polizas")] = caido

    respuesta = client.get("/v1/cliente/polizas", headers=_auth(client))

    assert respuesta.status_code == 503


def test_detalle_devuelve_la_poliza_con_quehacer(client, nucleo_polizas, nucleo_cotizacion):
    nucleo_polizas.respuestas[("GET", "/v1/polizas/numero/POL-88219-CO")] = lambda _: httpx.Response(
        200, json=POLIZA_SALIDA
    )
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/por-oferta/{OFERTA_ID}")] = lambda _: httpx.Response(
        200, json=COTIZACION_SALIDA
    )

    respuesta = client.get("/v1/cliente/polizas/POL-88219-CO", headers=_auth(client))

    assert respuesta.status_code == 200
    detalle = respuesta.json()
    assert detalle["numero"] == "POL-88219-CO"
    assert detalle["ramo"] == COTIZACION_SALIDA["producto"]
    assert detalle["queHacer"]
    assert detalle["coberturas"] == [{"nombre": "cobertura-base", "sumaAsegurada": 89000.0, "deducible": 0.0}]


def test_detalle_poliza_inexistente_es_404(client, nucleo_polizas):
    respuesta = client.get("/v1/cliente/polizas/POL-NO-EXISTE", headers=_auth(client))

    assert respuesta.status_code == 404


def test_detalle_servicio_no_disponible_es_503(client, nucleo_polizas):
    def caido(request):
        raise httpx.ConnectError("conexión rechazada", request=request)

    nucleo_polizas.respuestas[("GET", "/v1/polizas/numero/POL-88219-CO")] = caido

    respuesta = client.get("/v1/cliente/polizas/POL-88219-CO", headers=_auth(client))

    assert respuesta.status_code == 503


def test_pago_automatico_es_numero(client):
    body = client.get("/v1/cliente/pagos-automaticos", headers=_auth(client)).json()
    assert isinstance(body["monto"], int)
    assert body["moneda"] == "COP"
    assert "locale" not in body


OFERTA_HIPOTECARIA_ID = "77777777-7777-7777-7777-777777777777"

OFERTA_HIPOTECARIA_SALIDA = {
    "id": OFERTA_HIPOTECARIA_ID,
    "cliente_id": "cualquier-cliente",
    "precio": "64000.00",
    "moneda": "COP",
    "degradado": False,
    "factores": [
        {"factor": "plazo", "impacto": "positivo", "peso": "0.4000"},
        {"factor": "valor del crédito", "impacto": "negativo", "peso": "0.1000"},
    ],
    "snapshot_atributos": [],
    "creado_en": "2026-10-01T00:00:00Z",
}


def test_hipoteca_con_consentimiento_llama_a_perfilamiento(client, nucleo_perfilamiento):
    nucleo_perfilamiento.respuestas[("POST", "/v1/consentimientos")] = lambda _: httpx.Response(
        201, json={"id": "88888888-8888-8888-8888-888888888888", "cliente_id": "c", "otorgado_en": "2026-10-01T00:00:00Z", "revocado_en": None, "vigente": True}
    )
    nucleo_perfilamiento.respuestas[("POST", "/v1/ofertas-hipotecario")] = lambda _: httpx.Response(
        201, json=OFERTA_HIPOTECARIA_SALIDA
    )

    headers = _auth(client)
    ready = client.post(
        "/v1/cliente/oferta-hipotecaria",
        headers=headers,
        json={"credito": {"valor": 180000000, "plazoMeses": 180}, "consentimientoPerfil": True},
    )

    assert ready.status_code == 200
    body = ready.json()
    assert body["prima"] == 64000.0
    assert body["degradada"] is False
    assert body["moneda"] == "COP"
    assert body["factores"] == ["plazo", "valor del crédito"]

    # Se otorga el consentimiento antes de pedir la oferta.
    assert ("POST", "/v1/consentimientos") == (
        nucleo_perfilamiento.peticiones[0].method,
        nucleo_perfilamiento.peticiones[0].url.path,
    )


def test_hipoteca_sin_consentimiento_no_llama_a_perfilamiento(client, nucleo_perfilamiento):
    headers = _auth(client)
    degraded = client.post(
        "/v1/cliente/oferta-hipotecaria",
        headers=headers,
        json={"credito": {"valor": 180000000, "plazoMeses": 180}, "consentimientoPerfil": False},
    )

    assert degraded.status_code == 200
    body = degraded.json()
    assert body["prima"] == 50000 and body["degradada"] is True
    assert body["moneda"] == "COP"
    assert nucleo_perfilamiento.peticiones == []


def test_hipoteca_servicio_no_disponible_es_503(client, nucleo_perfilamiento):
    def caido(request):
        raise httpx.ConnectError("conexión rechazada", request=request)

    nucleo_perfilamiento.respuestas[("POST", "/v1/consentimientos")] = caido

    response = client.post(
        "/v1/cliente/oferta-hipotecaria",
        headers=_auth(client),
        json={"credito": {"valor": 180000000, "plazoMeses": 180}, "consentimientoPerfil": True},
    )
    assert response.status_code == 503


PRODUCTO_SALIDA = {
    "nombre": "Protección de dispositivo",
    "moneda": "COP",
    "coberturas": [
        {"codigo": "ROBO", "nombre": "Robo", "limite": "5000000.00", "unidad_limite": "COP"},
    ],
    "datos_riesgo": [
        {"nombre": "valorDispositivo", "tipo": "rango", "minimo": "500000", "maximo": "10000000"},
        {"nombre": "marca", "tipo": "lista", "valores": ["samsung", "apple", "xiaomi"]},
    ],
}


def test_catalogo_traduce_coberturas_y_datos_riesgo(client, nucleo_cotizacion):
    nucleo_cotizacion.respuestas[("GET", "/v1/productos/proteccion-dispositivo")] = lambda _: httpx.Response(
        200, json=PRODUCTO_SALIDA
    )

    response = client.get("/v1/cliente/catalogo/Protección de dispositivo", headers=_auth(client))
    assert response.status_code == 200
    body = response.json()
    assert body["ramo"] == "Protección de dispositivo"
    assert body["nombre"] == "Protección de dispositivo"
    assert body["moneda"] == "COP"
    assert body["coberturas"] == [
        {"codigo": "ROBO", "nombre": "Robo", "limite": "5000000.00", "unidadLimite": "COP"},
    ]
    assert body["datosRiesgo"] == [
        {"nombre": "valorDispositivo", "tipo": "rango", "minimo": "500000", "maximo": "10000000"},
        {"nombre": "marca", "tipo": "lista", "valores": ["samsung", "apple", "xiaomi"]},
    ]


def test_catalogo_producto_inexistente_es_404(client, nucleo_cotizacion):
    nucleo_cotizacion.respuestas[("GET", "/v1/productos/ramo-inventado")] = lambda _: httpx.Response(
        404, json={"codigo": "no_encontrado", "mensaje": "No existe"}
    )

    response = client.get("/v1/cliente/catalogo/ramo-inventado", headers=_auth(client))
    assert response.status_code == 404


def test_inicio(client):
    body = client.get("/v1/cliente/inicio", headers=_auth(client)).json()
    assert body["hipotecario"] is None


def test_sin_token_es_401(client):
    assert client.get("/v1/cliente/inicio").status_code == 401
