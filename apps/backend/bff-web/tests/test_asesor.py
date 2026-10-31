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

SUSCRIPCION_ACEPTADA = {
    "suscripcion_id": "44444444-4444-4444-4444-444444444444",
    "solicitud_id": COTIZACION_ID,
    "perfil_id": "55555555-5555-5555-5555-555555555555",
    "decision": "ACEPTADA",
    "motivo": "riesgo_aceptable",
    "evaluada_en": "2026-10-01T00:05:00Z",
    "regla": "Score de riesgo hasta 0.7000",
}

SUSCRIPCION_RECHAZADA = {**SUSCRIPCION_ACEPTADA, "decision": "RECHAZADA", "motivo": "score_fuera_de_apetito"}

ACEPTACION_SALIDA = {
    "cotizacion_id": COTIZACION_ID,
    "oferta_id": OFERTA_ID,
    "estado": "aceptada",
    "prima": "89000.00",
    "moneda": "COP",
    "aceptada_en": "2026-10-01T00:00:00Z",
    "suscripcion_id": SUSCRIPCION_ACEPTADA["suscripcion_id"],
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
    "id": "66666666-6666-6666-6666-666666666666",
    "numero": "POL-88219-CO",
    "oferta_id": OFERTA_ID,
    "usuario_id": "77777777-7777-7777-7777-777777777777",
    "inicio_vigencia": "2026-10-01T00:00:00Z",
    "fin_vigencia": "2027-10-01T00:00:00Z",
    "estado": "vigente",
    "coberturas": [{"nombre": "cobertura-base", "suma_asegurada": "89000.00", "deducible": "0"}],
}


FIRMA_SALIDA = {
    "oferta_id": OFERTA_ID,
    "resultado": "OK",
    "motivo": None,
    "firma_hash": "3f9a0c",
    "firmada_en": "2026-09-16T15:25:00Z",
}

FIRMA_FALLIDA = {"codigo": "firma_no_exitosa", "mensaje": "La firma electrónica no fue exitosa: Firma rechazada"}


def _auth(client, rol):
    return {"Authorization": f"Bearer {token(client, rol)}"}


def test_cartera_ficha_y_venta(client, nucleo_cotizacion):
    headers = _auth(client, "asesor")
    assert client.get("/v1/asesor/cartera", headers=headers).status_code == 200
    created = client.post(
        "/v1/asesor/clientes",
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
        "/v1/asesor/clientes/estado",
        headers=headers,
        json={"clienteId": "CLI-18", "estado": "inactivo"},
    )
    assert off.json()["estado"] == "inactivo"

    nucleo_cotizacion.respuestas[("POST", "/v1/cotizaciones")] = lambda _: httpx.Response(
        201, json=COTIZACION_SALIDA
    )
    sale = client.post(
        "/v1/asesor/cotizaciones",
        headers=headers,
        json={"clienteId": "CLI-18", "ramo": "Protección de dispositivo", "datosRiesgo": {}},
    )
    assert sale.status_code == 200
    venta = sale.json()
    assert isinstance(venta["prima"], str)
    assert venta["primaNeta"] == "80000.00"
    assert venta["expedicion"] == "9000.00"


PRODUCTO_SALIDA = {
    "nombre": "Protección de dispositivo",
    "moneda": "COP",
    "coberturas": [
        {"codigo": "ROBO", "nombre": "Robo", "limite": "5000000.00", "unidad_limite": "COP"},
    ],
    "datos_riesgo": [
        {"nombre": "valorDispositivo", "tipo": "rango", "minimo": "500000", "maximo": "10000000"},
    ],
}


def test_catalogo_de_asesor_traduce_coberturas_y_datos_riesgo(client, nucleo_cotizacion):
    nucleo_cotizacion.respuestas[("GET", "/v1/productos/proteccion-dispositivo")] = lambda _: httpx.Response(
        200, json=PRODUCTO_SALIDA
    )

    response = client.get(
        "/v1/asesor/catalogo/Protección de dispositivo",
        headers=_auth(client, "asesor"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ramo"] == "Protección de dispositivo"
    assert body["coberturas"] == [
        {"codigo": "ROBO", "nombre": "Robo", "limite": "5000000.00", "unidadLimite": "COP"},
    ]
    assert body["datosRiesgo"] == [
        {"nombre": "valorDispositivo", "tipo": "rango", "minimo": "500000", "maximo": "10000000"},
    ]


def test_consultar_emision_feliz_devuelve_decision_y_oferta(client, nucleo_cotizacion, nucleo_suscripcion):
    headers = _auth(client, "asesor")
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/{COTIZACION_ID}")] = lambda _: httpx.Response(
        200, json=COTIZACION_SALIDA
    )
    nucleo_suscripcion.respuestas[("POST", "/v1/suscripciones")] = lambda _: httpx.Response(
        201, json=SUSCRIPCION_ACEPTADA
    )

    nucleo_cotizacion.respuestas[("GET", "/v1/productos/proteccion-dispositivo")] = lambda _: httpx.Response(
        200, json=PRODUCTO_SALIDA
    )

    respuesta = client.post(
        "/v1/asesor/emisiones", headers=headers, json={"cotizacionId": COTIZACION_ID, "clienteId": "CLI-18"}
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["solicitudId"] == COTIZACION_ID
    assert cuerpo["cliente"] == {"clienteId": "CLI-18", "nombre": "Andrés Gómez"}
    assert cuerpo["producto"] == PRODUCTO_SALIDA["nombre"]
    assert cuerpo["referencia"] == COTIZACION_ID
    assert [(p["paso"], p["estado"]) for p in cuerpo["pasos"]][2] == ("EMISION", "ACTUAL")
    assert cuerpo["decision"]["resultado"] == "ACEPTADA"
    assert cuerpo["decision"]["detalle"] == "riesgo_aceptable"
    assert cuerpo["decision"]["regla"] == "Score de riesgo hasta 0.7000"
    assert cuerpo["decision"]["decididoPor"] == "Motor automático"
    assert cuerpo["oferta"]["moneda"] == "COP"
    assert cuerpo["oferta"]["primaTotal"] == "89000.00"
    assert cuerpo["oferta"]["vigenciaMeses"] == 12


def test_consultar_emision_sin_catalogo_muestra_el_codigo_del_producto(
    client, nucleo_cotizacion, nucleo_suscripcion
):
    headers = _auth(client, "asesor")
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/{COTIZACION_ID}")] = lambda _: httpx.Response(
        200, json=COTIZACION_SALIDA
    )
    nucleo_suscripcion.respuestas[("POST", "/v1/suscripciones")] = lambda _: httpx.Response(
        201, json=SUSCRIPCION_ACEPTADA
    )

    respuesta = client.post(
        "/v1/asesor/emisiones", headers=headers, json={"cotizacionId": COTIZACION_ID, "clienteId": "CLI-18"}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["producto"] == COTIZACION_SALIDA["producto"]


def test_consultar_emision_rechazada(client, nucleo_cotizacion, nucleo_suscripcion):
    headers = _auth(client, "asesor")
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/{COTIZACION_ID}")] = lambda _: httpx.Response(
        200, json=COTIZACION_SALIDA
    )
    nucleo_suscripcion.respuestas[("POST", "/v1/suscripciones")] = lambda _: httpx.Response(
        201, json=SUSCRIPCION_RECHAZADA
    )

    respuesta = client.post(
        "/v1/asesor/emisiones", headers=headers, json={"cotizacionId": COTIZACION_ID}
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["decision"]["resultado"] == "RECHAZADA"
    assert respuesta.json()["pasos"][2] == {"paso": "EMISION", "estado": "ERROR"}


def test_consultar_emision_cotizacion_inexistente_es_404(client, nucleo_cotizacion):
    respuesta = client.post(
        "/v1/asesor/emisiones", headers=_auth(client, "asesor"), json={"cotizacionId": COTIZACION_ID}
    )
    assert respuesta.status_code == 404


def test_firmar_y_emitir_feliz_encadena_aceptacion_pago_y_poliza(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas
):
    headers = _auth(client, "asesor")
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_SALIDA
    )
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/{COTIZACION_ID}")] = lambda _: httpx.Response(
        200, json=COTIZACION_SALIDA
    )
    nucleo_pagos.respuestas[("POST", "/v1/pagos/primas")] = lambda _: httpx.Response(201, json=PAGO_SALIDA)
    nucleo_polizas.respuestas[("POST", "/v1/polizas")] = lambda _: httpx.Response(201, json=POLIZA_SALIDA)
    nucleo_polizas.respuestas[("GET", f"/v1/polizas/firmas/{OFERTA_ID}")] = lambda _: httpx.Response(
        200, json=FIRMA_SALIDA
    )

    respuesta = client.post(f"/v1/asesor/emisiones/{COTIZACION_ID}/poliza", headers=headers)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["resultado"] == "EMITIDA"
    assert cuerpo["poliza"]["numero"] == "POL-88219-CO"
    assert cuerpo["poliza"]["ramo"] == COTIZACION_SALIDA["producto"]
    assert cuerpo["poliza"]["inicioVigencia"] == POLIZA_SALIDA["inicio_vigencia"]
    assert cuerpo["poliza"]["finVigencia"] == POLIZA_SALIDA["fin_vigencia"]
    assert cuerpo["poliza"]["expedidaEn"] == POLIZA_SALIDA["inicio_vigencia"]
    assert cuerpo["firma"] == {"firmadaEn": FIRMA_SALIDA["firmada_en"], "hash": FIRMA_SALIDA["firma_hash"]}
    assert cuerpo["pasos"][3] == {"paso": "POLIZA", "estado": "COMPLETADO"}


def test_firmar_y_emitir_con_decision_rechazada_no_cobra_ni_emite(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas
):
    headers = _auth(client, "asesor")
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_RECHAZADA
    )

    respuesta = client.post(f"/v1/asesor/emisiones/{COTIZACION_ID}/poliza", headers=headers)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"resultado": "RECHAZADA", "motivo": ACEPTACION_RECHAZADA["motivo"]}
    assert nucleo_pagos.peticiones == []
    assert nucleo_polizas.peticiones == []


def test_firmar_y_emitir_con_firma_fallida_responde_rechazo_con_motivo(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas
):
    headers = _auth(client, "asesor")
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_SALIDA
    )
    nucleo_pagos.respuestas[("POST", "/v1/pagos/primas")] = lambda _: httpx.Response(201, json=PAGO_SALIDA)
    nucleo_polizas.respuestas[("POST", "/v1/polizas")] = lambda _: httpx.Response(422, json=FIRMA_FALLIDA)

    respuesta = client.post(f"/v1/asesor/emisiones/{COTIZACION_ID}/poliza", headers=headers)

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "resultado": "RECHAZADA",
        "motivo": FIRMA_FALLIDA["mensaje"],
        "pasos": [
            {"paso": "COTIZAR", "estado": "COMPLETADO"},
            {"paso": "OFERTA", "estado": "COMPLETADO"},
            {"paso": "EMISION", "estado": "ERROR"},
            {"paso": "POLIZA", "estado": "PENDIENTE"},
        ],
    }


def test_firmar_y_emitir_propaga_otros_rechazos_del_nucleo(client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas):
    headers = _auth(client, "asesor")
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_SALIDA
    )
    nucleo_pagos.respuestas[("POST", "/v1/pagos/primas")] = lambda _: httpx.Response(201, json=PAGO_SALIDA)
    nucleo_polizas.respuestas[("POST", "/v1/polizas")] = lambda _: httpx.Response(
        422, json={"codigo": "sin_cobro_exitoso", "mensaje": "No hay cobro"}
    )

    respuesta = client.post(f"/v1/asesor/emisiones/{COTIZACION_ID}/poliza", headers=headers)

    assert respuesta.status_code == 422


def test_asesor_no_abre_otras_pantallas(client):
    headers = _auth(client, "asesor")
    assert client.get("/v1/cliente/inicio", headers=headers).status_code == 403
    assert client.get("/v1/operador/avisos", headers=headers).status_code == 403
    assert client.post(
        "/v1/operador/polizas/ciclo",
        headers=headers,
        json={"numero": "POL-1", "verbo": "renovar"},
    ).status_code == 403


def test_cliente_no_abre_pantallas_de_asesor(client):
    headers = _auth(client, "cliente")
    assert client.get("/v1/asesor/cartera", headers=headers).status_code == 403
    assert client.get("/v1/operador/avisos", headers=headers).status_code == 403


def test_listado_de_clientes_trae_canal_y_consentimiento(client):
    clientes = client.get("/v1/asesor/clientes", headers=_auth(client, "asesor")).json()["clientes"]
    assert len({item["clienteId"] for item in clientes}) == len(clientes) == 5
    assert {item["canal"] for item in clientes} == {"web", "android"}
    assert {item["estado"] for item in clientes} == {"activo", "inactivo"}
    revocado = next(item for item in clientes if item["consentimiento"] == "revocado")
    assert revocado["habeasData"] is False


# --- HU-163 (SOLV-262): cotizaciones pendientes del asesor ---------------

import json  # noqa: E402
import uuid  # noqa: E402

from app.routers.cliente import _NAMESPACE_SOLVENTA  # noqa: E402

OFERTA_EMITIDA = "aaaaaaaa-0000-0000-0000-000000000001"
OFERTA_SIN_POLIZA = "aaaaaaaa-0000-0000-0000-000000000002"
OFERTA_COTIZADA = "aaaaaaaa-0000-0000-0000-000000000003"


def _item(cotizacion_id: str, oferta_id: str, estado: str) -> dict:
    return {
        **COTIZACION_SALIDA,
        "cotizacion_id": cotizacion_id,
        "estado": estado,
        "oferta_id": oferta_id,
        "cliente_ref": "CLI-18",
    }


LISTADO = {
    "items": [
        _item("c0000000-0000-0000-0000-000000000001", OFERTA_EMITIDA, "aceptada"),
        _item("c0000000-0000-0000-0000-000000000002", OFERTA_SIN_POLIZA, "aceptada"),
        _item("c0000000-0000-0000-0000-000000000003", OFERTA_COTIZADA, "cotizada"),
    ],
    "pagina": 1,
    "tamano": 20,
    "hay_mas": True,
}


def _asesor_id(correo: str = "persona@solventa.com") -> str:
    return str(uuid.uuid5(_NAMESPACE_SOLVENTA, f"asesor|{correo}"))


def _listado(nucleo_cotizacion, cuerpo=LISTADO):
    nucleo_cotizacion.respuestas[("GET", "/v1/cotizaciones")] = lambda _: httpx.Response(200, json=cuerpo)


def test_venta_envia_asesor_de_la_sesion_y_cliente_ref(client, nucleo_cotizacion):
    nucleo_cotizacion.respuestas[("POST", "/v1/cotizaciones")] = lambda _: httpx.Response(
        201, json=COTIZACION_SALIDA
    )
    respuesta = client.post(
        "/v1/asesor/cotizaciones",
        headers=_auth(client, "asesor"),
        json={
            "clienteId": "CLI-18",
            "ramo": "Protección de dispositivo",
            "datosRiesgo": {},
            "asesor_id": "99999999-9999-9999-9999-999999999999",
            "asesorId": "99999999-9999-9999-9999-999999999999",
        },
    )
    assert respuesta.status_code == 200
    enviado = json.loads(nucleo_cotizacion.peticiones[-1].content)
    assert enviado["asesor_id"] == _asesor_id()
    assert enviado["cliente_ref"] == "CLI-18"


def test_venta_conserva_la_respuesta_previa(client, nucleo_cotizacion):
    nucleo_cotizacion.respuestas[("POST", "/v1/cotizaciones")] = lambda _: httpx.Response(
        201, json=COTIZACION_SALIDA
    )
    respuesta = client.post(
        "/v1/asesor/cotizaciones",
        headers=_auth(client, "asesor"),
        json={"clienteId": "CLI-18", "ramo": "Protección de dispositivo", "datosRiesgo": {}},
    )
    from app.routers.cliente import _cotizacion_salida

    assert respuesta.json() == _cotizacion_salida(COTIZACION_SALIDA, "Protección de dispositivo")
    enviado = json.loads(nucleo_cotizacion.peticiones[-1].content)
    assert enviado["canal"] == "asesor"
    assert enviado["producto"] == "proteccion-dispositivo"


def test_pendientes_filtra_por_asesor_y_reenvia_paginacion(client, nucleo_cotizacion, nucleo_polizas):
    _listado(nucleo_cotizacion, {**LISTADO, "items": []})
    respuesta = client.get(
        "/v1/asesor/cotizaciones?incluirVencidas=true&pagina=3&tamano=5",
        headers=_auth(client, "asesor"),
    )
    assert respuesta.status_code == 200
    params = nucleo_cotizacion.peticiones[-1].url.params
    assert params["asesor_id"] == _asesor_id()
    assert params["estados"] == "cotizada,aceptada"
    assert params["incluir_vencidas"] == "true"
    assert params["pagina"] == "3"
    assert params["tamano"] == "5"


def test_pendientes_por_defecto_oculta_vencidas(client, nucleo_cotizacion):
    _listado(nucleo_cotizacion, {**LISTADO, "items": []})
    client.get("/v1/asesor/cotizaciones", headers=_auth(client, "asesor"))
    params = nucleo_cotizacion.peticiones[-1].url.params
    assert params["incluir_vencidas"] == "false"
    assert params["pagina"] == "1"
    assert params["tamano"] == "20"


def test_pendientes_traduce_campos_y_descarta_aceptadas_con_poliza(client, nucleo_cotizacion, nucleo_polizas):
    _listado(nucleo_cotizacion)
    nucleo_polizas.respuestas[("GET", "/v1/polizas/por-ofertas")] = lambda _: httpx.Response(
        200, json={"oferta_ids_con_poliza": [OFERTA_EMITIDA]}
    )
    respuesta = client.get("/v1/asesor/cotizaciones", headers=_auth(client, "asesor"))
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [i["ofertaId"] for i in cuerpo["items"]] == [OFERTA_SIN_POLIZA, OFERTA_COTIZADA]
    assert cuerpo["items"][0] == {
        "cotizacionId": "c0000000-0000-0000-0000-000000000002",
        "ofertaId": OFERTA_SIN_POLIZA,
        "ramo": "Protección de dispositivo",
        "estado": "aceptada",
        "prima": "89000.00",
        "moneda": "COP",
        "creadaEn": "2026-10-01T00:00:00Z",
        "venceEn": "2026-11-01T00:00:00Z",
        "vencida": False,
        "clienteRef": "CLI-18",
    }
    assert cuerpo["pagina"] == 1
    assert cuerpo["tamano"] == 20
    assert cuerpo["hayMas"] is True
    assert cuerpo["avisos"] == []

    consultas = [p for p in nucleo_polizas.peticiones if p.url.path == "/v1/polizas/por-ofertas"]
    assert len(consultas) == 1
    assert consultas[0].url.params["oferta_ids"] == f"{OFERTA_EMITIDA},{OFERTA_SIN_POLIZA}"


def test_pendientes_sin_aceptadas_no_consulta_polizas(client, nucleo_cotizacion, nucleo_polizas):
    _listado(nucleo_cotizacion, {**LISTADO, "items": [LISTADO["items"][2]]})
    respuesta = client.get("/v1/asesor/cotizaciones", headers=_auth(client, "asesor"))
    assert [i["estado"] for i in respuesta.json()["items"]] == ["cotizada"]
    assert nucleo_polizas.peticiones == []


def test_pendientes_sin_ms_polizas_lista_solo_cotizadas_con_aviso(client, nucleo_cotizacion, nucleo_polizas):
    _listado(nucleo_cotizacion)
    nucleo_polizas.respuestas[("GET", "/v1/polizas/por-ofertas")] = lambda _: httpx.Response(503)
    respuesta = client.get("/v1/asesor/cotizaciones", headers=_auth(client, "asesor"))
    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [i["estado"] for i in cuerpo["items"]] == ["cotizada"]
    assert cuerpo["avisos"] == ["polizas_no_disponible"]


def test_pendientes_sin_ms_cotizacion_responde_503(client, nucleo_cotizacion):
    nucleo_cotizacion.respuestas[("GET", "/v1/cotizaciones")] = lambda _: httpx.Response(503)
    respuesta = client.get("/v1/asesor/cotizaciones", headers=_auth(client, "asesor"))
    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "servicio_no_disponible"


def test_operador_no_lista_cotizaciones_pendientes(client):
    assert client.get("/v1/asesor/cotizaciones", headers=_auth(client, "operador")).status_code == 403
