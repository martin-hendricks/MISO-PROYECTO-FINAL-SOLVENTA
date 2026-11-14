import asyncio
import json
import time

import httpx
import pytest

from app.dependencies import issue_pair
from app.routers.cliente import _tarjeta, contexto_canonico

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
    "usuario_id": "11111111-1111-1111-1111-111111111111",
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


def test_emision_rechaza_datos_de_tarjeta(client):
    response = client.post(
        "/v1/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": COTIZACION_ID, "numeroTarjeta": "4242424242424242"},
    )
    assert response.status_code == 422


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
    assert body["poliza"]["ramo"] == "Protección de dispositivo"
    assert body["poliza"]["producto"] == "Protección de dispositivo"
    assert body["poliza"]["descripcion"] == (
        "Cubre robo, daño accidental y reposición del equipo asegurado."
    )
    assert body["poliza"]["inicioVigencia"] == POLIZA_SALIDA["inicio_vigencia"]
    assert body["poliza"]["finVigencia"] == POLIZA_SALIDA["fin_vigencia"]
    assert body["poliza"]["moneda"] == ACEPTACION_SALIDA["moneda"]
    assert body["poliza"]["primaTotal"] == float(ACEPTACION_SALIDA["prima"])

    pago_enviado = nucleo_pagos.peticiones[-1]
    assert pago_enviado is not None
    poliza_enviada = nucleo_polizas.peticiones[-1]
    import json as _json

    assert _json.loads(poliza_enviada.read())["token_pago_confirmado"] == PAGO_ID


def _emision_responde(nucleo_cotizacion, nucleo_pagos, nucleo_polizas, producto: str) -> None:
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        201, json=ACEPTACION_SALIDA
    )
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/{COTIZACION_ID}")] = lambda _: httpx.Response(
        200, json={**COTIZACION_SALIDA, "producto": producto}
    )
    nucleo_pagos.respuestas[("POST", "/v1/pagos/primas")] = lambda _: httpx.Response(201, json=PAGO_SALIDA)
    nucleo_polizas.respuestas[("POST", "/v1/polizas")] = lambda _: httpx.Response(201, json=POLIZA_SALIDA)


def test_emision_reintentada_envia_la_misma_clave_de_idempotencia(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas
):
    """La aceptación se confirma en ms-cotizacion antes de llamar a ms-suscripcion:
    la clave debe derivarse de la cotización para que un reintento tras una falla
    técnica no queme la oferta con `oferta_ya_usada`."""
    _emision_responde(nucleo_cotizacion, nucleo_pagos, nucleo_polizas, "proteccion-dispositivo")

    for _ in range(2):
        respuesta = client.post("/v1/cliente/polizas", headers=_auth(client), json={"cotizacionId": COTIZACION_ID})
        assert respuesta.status_code == 200

    claves = [
        p.headers["Idempotency-Key"]
        for p in _ruta(nucleo_cotizacion.peticiones, "POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")
    ]
    assert len(claves) == 2
    assert claves[0] == claves[1]


def test_emitir_vida_hipotecario_cierra_la_originacion(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas, nucleo_perfilamiento
):
    _emision_responde(nucleo_cotizacion, nucleo_pagos, nucleo_polizas, "vida-hipotecario")
    ruta = f"/v1/originaciones/clientes/{_usuario_id()}/pendiente"
    nucleo_perfilamiento.respuestas[("DELETE", ruta)] = lambda _: httpx.Response(204)

    response = client.post("/v1/cliente/polizas", headers=_auth(client), json={"cotizacionId": COTIZACION_ID})

    assert response.json()["resultado"] == "EMITIDA"
    assert len(_ruta(nucleo_perfilamiento.peticiones, "DELETE", ruta)) == 1


def test_emitir_si_no_se_puede_cerrar_la_originacion_igual_queda_emitida(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas, nucleo_perfilamiento
):
    _emision_responde(nucleo_cotizacion, nucleo_pagos, nucleo_polizas, "vida-hipotecario")
    nucleo_perfilamiento.respuestas[("DELETE", f"/v1/originaciones/clientes/{_usuario_id()}/pendiente")] = _caido

    response = client.post("/v1/cliente/polizas", headers=_auth(client), json={"cotizacionId": COTIZACION_ID})

    assert response.status_code == 200
    assert response.json()["resultado"] == "EMITIDA"


def test_emitir_otro_ramo_no_toca_la_originacion(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas, nucleo_perfilamiento
):
    _emision_responde(nucleo_cotizacion, nucleo_pagos, nucleo_polizas, "proteccion-dispositivo")

    client.post("/v1/cliente/polizas", headers=_auth(client), json={"cotizacionId": COTIZACION_ID})

    assert nucleo_perfilamiento.peticiones == []


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


def test_emision_con_consentimiento_revocado_se_propaga_sin_cobrar(
    client, nucleo_cotizacion, nucleo_pagos, nucleo_polizas
):
    cuerpo = {"codigo": "consentimiento_revocado", "mensaje": "El consentimiento ya no está vigente; vuelva a cotizar"}
    nucleo_cotizacion.respuestas[("POST", f"/v1/cotizaciones/{COTIZACION_ID}/aceptacion")] = lambda _: httpx.Response(
        422, json=cuerpo
    )

    response = client.post(
        "/v1/cliente/polizas",
        headers=_auth(client),
        json={"cotizacionId": COTIZACION_ID},
    )

    assert response.status_code == 422
    assert response.json() == cuerpo
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
    assert polizas[0]["producto"] == "Protección de dispositivo"
    assert polizas[0]["inicioVigencia"] == POLIZA_SALIDA["inicio_vigencia"]
    assert polizas[0]["finVigencia"] == POLIZA_SALIDA["fin_vigencia"]
    assert polizas[0]["moneda"] == "COP"
    assert polizas[0]["primaTotal"] == 89000.0
    assert polizas[0]["ramo"] == "Protección de dispositivo"
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
    assert detalle["ramo"] == "Protección de dispositivo"
    assert detalle["queHacer"]
    assert detalle["coberturas"] == [{"nombre": "cobertura-base", "sumaAsegurada": 89000.0, "deducible": 0.0}]


def test_detalle_de_otro_cliente_es_404(client, nucleo_polizas):
    ajena = {**POLIZA_SALIDA, "usuario_id": "99999999-9999-9999-9999-999999999999"}
    nucleo_polizas.respuestas[("GET", "/v1/polizas/numero/POL-88219-CO")] = lambda _: httpx.Response(
        200, json=ajena
    )
    assert client.get("/v1/cliente/polizas/POL-88219-CO", headers=_auth(client)).status_code == 404


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
    "precio": "42700.00",
    "moneda": "COP",
    "degradado": False,
    "factor_ajuste": "0.854",
    "factores": [
        {"factor": "score_comportamiento", "impacto": "reduce_prima", "peso": "-0.15"},
        {"factor": "zona_riesgo", "impacto": "aumenta_prima", "peso": "0.20"},
    ],
    "snapshot_atributos": [],
    "creado_en": "2026-10-01T00:00:00Z",
}

COTIZACION_VIDA_SALIDA = {
    **COTIZACION_SALIDA,
    "producto": "vida-hipotecario",
    "prima": "140100.00",
    "prima_neta": "128100.00",
    "gastos_expedicion": "12000.00",
    "factor_riesgo_origen": "real",
}

CREDITO = {"valor": 180000000, "plazoMeses": 180}

ORIGINACION_ID = "77777777-7777-7777-7777-777777777777"


def _originacion(valor: str = "180000000.00", plazo: int = 180, origen: str = "cliente") -> dict:
    return {
        "id": ORIGINACION_ID,
        "cliente_id": "c",
        "valor": valor,
        "plazo_meses": plazo,
        "origen": origen,
        "creada_en": "2026-11-05T00:00:00Z",
        "pendiente": True,
    }


def _ruta(peticiones, metodo: str, ruta: str) -> list:
    return [p for p in peticiones if (p.method, p.url.path) == (metodo, ruta)]


UID_SESION = "11111111-1111-1111-1111-111111111111"


def _usuario_id(uid: str = UID_SESION) -> str:
    return str(contexto_canonico({"uid": uid}).usuario_id)


def _perfilamiento_responde(nucleo_perfilamiento, oferta: dict = OFERTA_HIPOTECARIA_SALIDA) -> None:
    nucleo_perfilamiento.respuestas[("POST", "/v1/consentimientos")] = lambda _: httpx.Response(
        201,
        json={
            "id": "88888888-8888-8888-8888-888888888888",
            "cliente_id": "c",
            "otorgado_en": "2026-10-01T00:00:00Z",
            "revocado_en": None,
            "vigente": True,
        },
    )
    nucleo_perfilamiento.respuestas[("POST", "/v1/ofertas-hipotecario")] = lambda _: httpx.Response(201, json=oferta)
    nucleo_perfilamiento.respuestas[("POST", "/v1/originaciones")] = lambda _: httpx.Response(
        201, json=_originacion()
    )


def _cotizacion_vida_responde(nucleo_cotizacion, salida: dict = COTIZACION_VIDA_SALIDA) -> None:
    nucleo_cotizacion.respuestas[("POST", "/v1/cotizaciones")] = lambda _: httpx.Response(201, json=salida)


def _caido(request):
    raise httpx.ConnectError("conexión rechazada", request=request)


def _pedir_oferta(client, consentimiento: bool = True, credito: dict = CREDITO, headers: dict | None = None):
    return client.post(
        "/v1/cliente/oferta-hipotecaria",
        headers=headers or _auth(client),
        json={"credito": credito, "consentimientoPerfil": consentimiento},
    )


def test_hipoteca_perfila_y_cotiza_vida_hipotecario_con_el_mismo_cliente(
    client, nucleo_perfilamiento, nucleo_cotizacion
):
    _perfilamiento_responde(nucleo_perfilamiento)
    _cotizacion_vida_responde(nucleo_cotizacion)

    response = _pedir_oferta(client)

    assert response.status_code == 200
    body = response.json()
    # La prima es la de la cotización: es la que se cobra al emitir con este id (HU-114).
    assert body["cotizacionId"] == COTIZACION_ID
    assert body["prima"] == "140100.00"
    assert body["ramo"] == "Vida hipotecario"
    assert body["degradada"] is False
    assert body["credito"] == CREDITO
    assert body["factores"] == [
        {"factor": "score_comportamiento", "impacto": "reduce_prima"},
        {"factor": "zona_riesgo", "impacto": "aumenta_prima"},
    ]

    # Se otorga el consentimiento antes de perfilar, para el cliente de la sesión.
    (consentimiento,) = _ruta(nucleo_perfilamiento.peticiones, "POST", "/v1/consentimientos")
    (perfil,) = _ruta(nucleo_perfilamiento.peticiones, "POST", "/v1/ofertas-hipotecario")
    assert json.loads(consentimiento.read())["cliente_id"] == _usuario_id()
    assert json.loads(perfil.read())["cliente_id"] == _usuario_id()

    # ms-cotizacion recibe el mismo usuario_id: con él lee el perfil (IPerfilRiesgo).
    cotizacion = json.loads(nucleo_cotizacion.peticiones[-1].read())
    assert cotizacion["producto"] == "vida-hipotecario"
    assert cotizacion["usuario_id"] == _usuario_id()
    assert cotizacion["canal"] == "web"
    assert cotizacion["datos_riesgo"] == {"valor": 180000000, "plazoMeses": 180}
    # La cotización queda atada a la originación: autorizar de nuevo no la duplica.
    assert nucleo_cotizacion.peticiones[-1].headers["Idempotency-Key"] == f"originacion-{ORIGINACION_ID}"
    (registrada,) = _ruta(nucleo_perfilamiento.peticiones, "POST", "/v1/originaciones")
    assert json.loads(registrada.read()) == {
        "cliente_id": _usuario_id(),
        "valor": "180000000",
        "plazo_meses": 180,
        "origen": "cliente",
    }


def test_hipoteca_reutiliza_la_originacion_pendiente_con_los_mismos_valores(
    client, nucleo_perfilamiento, nucleo_cotizacion
):
    _perfilamiento_responde(nucleo_perfilamiento)
    _cotizacion_vida_responde(nucleo_cotizacion)
    nucleo_perfilamiento.respuestas[
        ("GET", f"/v1/originaciones/clientes/{_usuario_id()}/pendiente")
    ] = lambda _: httpx.Response(200, json=_originacion())

    _pedir_oferta(client)
    _pedir_oferta(client)

    assert _ruta(nucleo_perfilamiento.peticiones, "POST", "/v1/originaciones") == []
    claves = {p.headers["Idempotency-Key"] for p in _ruta(nucleo_cotizacion.peticiones, "POST", "/v1/cotizaciones")}
    assert claves == {f"originacion-{ORIGINACION_ID}"}


def test_hipoteca_con_otros_valores_registra_una_originacion_nueva(client, nucleo_perfilamiento, nucleo_cotizacion):
    _perfilamiento_responde(nucleo_perfilamiento)
    _cotizacion_vida_responde(nucleo_cotizacion)
    nucleo_perfilamiento.respuestas[
        ("GET", f"/v1/originaciones/clientes/{_usuario_id()}/pendiente")
    ] = lambda _: httpx.Response(200, json=_originacion(valor="90000000.00", plazo=120))

    _pedir_oferta(client)

    (registrada,) = _ruta(nucleo_perfilamiento.peticiones, "POST", "/v1/originaciones")
    assert json.loads(registrada.read())["plazo_meses"] == 180


def test_registrar_originacion_del_cliente(client, nucleo_perfilamiento):
    nucleo_perfilamiento.respuestas[("POST", "/v1/originaciones")] = lambda _: httpx.Response(
        201, json=_originacion(valor="250000000.00", plazo=240)
    )

    response = client.post(
        "/v1/cliente/originacion-hipotecaria",
        headers=_auth(client),
        json={"valor": 250000000, "plazoMeses": 240},
    )

    assert response.status_code == 201
    assert response.json() == {"valor": 250000000, "plazoMeses": 240, "origen": "cliente"}
    (registrada,) = nucleo_perfilamiento.peticiones
    assert json.loads(registrada.read()) == {
        "cliente_id": _usuario_id(),
        "valor": "250000000",
        "plazo_meses": 240,
        "origen": "cliente",
    }


def test_registrar_originacion_invalida_es_422_sin_llamar_al_nucleo(client, nucleo_perfilamiento):
    response = client.post(
        "/v1/cliente/originacion-hipotecaria",
        headers=_auth(client),
        json={"valor": 0, "plazoMeses": 240},
    )

    assert response.status_code == 422
    assert nucleo_perfilamiento.peticiones == []


def test_consultar_originacion_pendiente_del_cliente(client, nucleo_perfilamiento):
    nucleo_perfilamiento.respuestas[
        ("GET", f"/v1/originaciones/clientes/{_usuario_id()}/pendiente")
    ] = lambda _: httpx.Response(200, json=_originacion(origen="socio"))

    response = client.get("/v1/cliente/originacion-hipotecaria", headers=_auth(client))

    assert response.status_code == 200
    assert response.json() == {"valor": 180000000, "plazoMeses": 180, "origen": "socio"}


def test_sin_originacion_pendiente_es_404(client, nucleo_perfilamiento):
    response = client.get("/v1/cliente/originacion-hipotecaria", headers=_auth(client))

    assert response.status_code == 404


def _consentimiento(revocado_en: str | None = None) -> dict:
    return {
        "id": "88888888-8888-8888-8888-888888888888",
        "cliente_id": _usuario_id(),
        "otorgado_en": "2026-10-01T10:00:00Z",
        "revocado_en": revocado_en,
        "vigente": revocado_en is None,
    }


def test_consultar_consentimiento_perfil_vigente(client, nucleo_perfilamiento):
    nucleo_perfilamiento.respuestas[("GET", f"/v1/consentimientos/{_usuario_id()}")] = lambda _: httpx.Response(
        200, json=_consentimiento()
    )

    response = client.get("/v1/cliente/consentimiento-perfil", headers=_auth(client))

    assert response.status_code == 200
    assert response.json() == {"estado": "vigente", "otorgadoEn": "2026-10-01T10:00:00Z"}
    assert [(p.method, p.url.path) for p in nucleo_perfilamiento.peticiones] == [
        ("GET", f"/v1/consentimientos/{_usuario_id()}")
    ]


def test_consultar_sin_consentimiento_perfil(client, nucleo_perfilamiento):
    response = client.get("/v1/cliente/consentimiento-perfil", headers=_auth(client))

    assert response.status_code == 200
    assert response.json() == {"estado": "sin_consentimiento"}


def test_consultar_consentimiento_perfil_con_perfilamiento_caido_es_503(client, nucleo_perfilamiento):
    nucleo_perfilamiento.respuestas[("GET", f"/v1/consentimientos/{_usuario_id()}")] = _caido

    response = client.get("/v1/cliente/consentimiento-perfil", headers=_auth(client))

    assert response.status_code == 503


def test_revocar_consentimiento_perfil(client, nucleo_perfilamiento):
    nucleo_perfilamiento.respuestas[("DELETE", f"/v1/consentimientos/{_usuario_id()}")] = lambda _: httpx.Response(
        200, json=_consentimiento(revocado_en="2026-11-11T15:30:00Z")
    )

    response = client.delete("/v1/cliente/consentimiento-perfil", headers=_auth(client))

    assert response.status_code == 200
    assert response.json() == {"estado": "revocado", "revocadoEn": "2026-11-11T15:30:00Z"}
    assert [(p.method, p.url.path) for p in nucleo_perfilamiento.peticiones] == [
        ("DELETE", f"/v1/consentimientos/{_usuario_id()}")
    ]


def test_revocar_sin_consentimiento_perfil_vigente(client, nucleo_perfilamiento):
    response = client.delete("/v1/cliente/consentimiento-perfil", headers=_auth(client))

    assert response.status_code == 200
    assert response.json() == {"estado": "sin_consentimiento"}


def test_revocar_consentimiento_perfil_usa_la_identidad_de_la_sesion(client, nucleo_perfilamiento):
    uid = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    acceso = issue_pair("ana@correo.com", "cliente", uid)["accessToken"]

    client.delete("/v1/cliente/consentimiento-perfil", headers={"Authorization": f"Bearer {acceso}"})

    (revocada,) = nucleo_perfilamiento.peticiones
    assert revocada.url.path == f"/v1/consentimientos/{_usuario_id(uid)}"


def test_consentimiento_perfil_exige_rol_cliente(client, nucleo_perfilamiento):
    consulta = client.get("/v1/cliente/consentimiento-perfil", headers=_auth(client, "asesor"))
    revocacion = client.delete("/v1/cliente/consentimiento-perfil", headers=_auth(client, "asesor"))

    assert (consulta.status_code, revocacion.status_code) == (403, 403)
    assert nucleo_perfilamiento.peticiones == []


def test_hipoteca_usa_la_identidad_de_cada_sesion(client, nucleo_perfilamiento, nucleo_cotizacion):
    _perfilamiento_responde(nucleo_perfilamiento)
    _cotizacion_vida_responde(nucleo_cotizacion)

    sesiones = (("ana@correo.com", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"), ("beto@correo.com", "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"))
    for correo, uid in sesiones:
        acceso = issue_pair(correo, "cliente", uid)["accessToken"]
        _pedir_oferta(client, headers={"Authorization": f"Bearer {acceso}"})

    consentimientos = _ruta(nucleo_perfilamiento.peticiones, "POST", "/v1/consentimientos")
    assert [json.loads(p.read())["cliente_id"] for p in consentimientos] == [
        _usuario_id("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
        _usuario_id("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"),
    ]


def test_hipoteca_sin_consentimiento_no_llama_a_ningun_servicio(client, nucleo_perfilamiento, nucleo_cotizacion):
    response = _pedir_oferta(client, consentimiento=False)

    assert response.status_code == 200
    assert response.json() == {"ramo": "Vida hipotecario", "estado": "sin_consentimiento"}
    assert nucleo_perfilamiento.peticiones == []
    assert nucleo_cotizacion.peticiones == []


def test_hipoteca_perfil_degradado_marca_la_oferta(client, nucleo_perfilamiento, nucleo_cotizacion):
    _perfilamiento_responde(nucleo_perfilamiento, {**OFERTA_HIPOTECARIA_SALIDA, "degradado": True})
    _cotizacion_vida_responde(nucleo_cotizacion)

    body = _pedir_oferta(client).json()

    assert body["degradada"] is True
    assert body["cotizacionId"] == COTIZACION_ID


def test_hipoteca_factor_de_respaldo_en_cotizacion_marca_la_oferta(client, nucleo_perfilamiento, nucleo_cotizacion):
    _perfilamiento_responde(nucleo_perfilamiento)
    _cotizacion_vida_responde(nucleo_cotizacion, {**COTIZACION_VIDA_SALIDA, "factor_riesgo_origen": "respaldo"})

    assert _pedir_oferta(client).json()["degradada"] is True


def test_hipoteca_perfilamiento_caido_no_cancela_la_originacion(client, nucleo_perfilamiento, nucleo_cotizacion):
    nucleo_perfilamiento.respuestas[("POST", "/v1/consentimientos")] = _caido
    nucleo_perfilamiento.respuestas[
        ("GET", f"/v1/originaciones/clientes/{_usuario_id()}/pendiente")
    ] = _caido
    _cotizacion_vida_responde(nucleo_cotizacion, {**COTIZACION_VIDA_SALIDA, "factor_riesgo_origen": "respaldo"})

    response = _pedir_oferta(client)

    assert response.status_code == 200
    body = response.json()
    assert body["degradada"] is True
    assert body["factores"] == []
    assert body["cotizacionId"] == COTIZACION_ID


def test_hipoteca_cotizacion_caida_es_503(client, nucleo_perfilamiento, nucleo_cotizacion):
    _perfilamiento_responde(nucleo_perfilamiento)
    nucleo_cotizacion.respuestas[("POST", "/v1/cotizaciones")] = _caido

    assert _pedir_oferta(client).status_code == 503


def test_hipoteca_credito_invalido_es_422(client, nucleo_perfilamiento):
    response = _pedir_oferta(client, credito={"valor": 0, "plazoMeses": 180})

    assert response.status_code == 422
    assert nucleo_perfilamiento.peticiones == []


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


def test_un_nucleo_lento_no_agota_el_presupuesto_del_inicio(monkeypatch):
    monkeypatch.setattr("app.routers.cliente.CORTE_INICIO_S", 0.05)

    async def correr():
        async def lenta():
            await asyncio.Event().wait()
            return {"items": [{"cotizacion_id": "COT-lenta"}]}

        async def rapida():
            return [{"numero": "POL-1", "estado": "VIGENTE"}]

        inicio = time.monotonic()
        pagina, filas = await asyncio.gather(_tarjeta(lenta()), _tarjeta(rapida()))
        return time.monotonic() - inicio, pagina, filas

    elapsed, pagina, filas = asyncio.run(correr())
    assert pagina is None
    assert filas == [{"numero": "POL-1", "estado": "VIGENTE"}]
    assert elapsed < 0.5


def test_inicio_sin_originacion_no_ofrece_vida_hipotecario(client):
    body = client.get("/v1/cliente/inicio", headers=_auth(client)).json()
    assert body["hipotecario"] is None


def test_inicio_con_originacion_pendiente_ofrece_continuar_con_sus_valores(client, nucleo_perfilamiento):
    nucleo_perfilamiento.respuestas[
        ("GET", f"/v1/originaciones/clientes/{_usuario_id()}/pendiente")
    ] = lambda _: httpx.Response(200, json=_originacion(origen="socio"))

    body = client.get("/v1/cliente/inicio", headers=_auth(client)).json()

    assert body["hipotecario"] == {"estado": "disponible", "valor": 180000000, "plazoMeses": 180, "origen": "socio"}


def test_inicio_no_lista_cotizaciones_hipotecarias_como_pendientes(client, nucleo_cotizacion):
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/por-usuario/{UID_SESION}")] = lambda _: httpx.Response(
        200,
        json={
            "items": [
                {"cotizacion_id": "COT-H", "producto": "vida-hipotecario", "vence_en": "2999-06-01T12:00:00Z"},
                {"cotizacion_id": "COT-C", "producto": "vida-crediticia", "vence_en": "2999-06-01T12:00:00Z"},
                {"cotizacion_id": "COT-1", "producto": "proteccion-dispositivo", "vence_en": "2999-06-01T12:00:00Z"},
            ]
        },
    )

    body = client.get("/v1/cliente/inicio", headers=_auth(client)).json()

    assert [p["cotizacionId"] for p in body["cotizacionesPendientes"]] == ["COT-1"]
    assert body["ofertaVigente"]["cotizacionId"] == "COT-1"


UID = "11111111-1111-1111-1111-111111111111"


def test_inicio_proyecta_cotizacion_poliza_y_siniestro(
    client, nucleo_cotizacion, nucleo_polizas, nucleo_siniestros
):
    nucleo_cotizacion.respuestas[("GET", f"/v1/cotizaciones/por-usuario/{UID}")] = lambda _: httpx.Response(
        200,
        json={
            "items": [
                {
                    "cotizacion_id": "COT-1",
                    "producto": "proteccion-dispositivo",
                    "vence_en": "2999-06-01T12:00:00Z",
                }
            ]
        },
    )
    nucleo_polizas.respuestas[("GET", "/v1/polizas")] = lambda _: httpx.Response(
        200,
        json=[
            {
                "numero": "POL-1",
                "estado": "VIGENTE",
                "oferta_id": "22222222-2222-2222-2222-222222222222",
            }
        ],
    )
    nucleo_cotizacion.respuestas[
        ("GET", "/v1/cotizaciones/por-oferta/22222222-2222-2222-2222-222222222222")
    ] = lambda _: httpx.Response(200, json={"producto": "soat-motocicleta"})
    nucleo_siniestros.respuestas[("GET", "/v1/siniestros")] = lambda _: httpx.Response(
        200, json=[{"id": "SIN-1", "estado": "recibido"}]
    )

    body = client.get("/v1/cliente/inicio", headers=_auth(client)).json()

    assert body["ofertaVigente"] == {
        "cotizacionId": "COT-1",
        "ramo": "Protección de dispositivo",
        "estado": "oferta_vigente",
        "venceEn": "2999-06-01T12:00:00Z",
    }
    assert body["poliza"] == {"numero": "POL-1", "ramo": "SOAT motocicleta", "estado": "vigente"}
    assert body["siniestroEnCurso"] == {"siniestroId": "SIN-1", "estado": "recibido"}


def test_inicio_propaga_una_forma_que_no_es_del_nucleo(
    client, nucleo_cotizacion, nucleo_polizas, nucleo_siniestros
):
    headers = _auth(client)
    lista = ("GET", f"/v1/cotizaciones/por-usuario/{UID}")
    nucleo_cotizacion.respuestas[lista] = lambda _: httpx.Response(200, json=["no-es-pagina"])
    with pytest.raises(AttributeError):
        client.get("/v1/cliente/inicio", headers=headers)

    nucleo_cotizacion.respuestas[lista] = lambda _: httpx.Response(200, json={"items": []})
    nucleo_polizas.respuestas[("GET", "/v1/polizas")] = lambda _: httpx.Response(200, json={"numero": "x"})
    with pytest.raises(KeyError):
        client.get("/v1/cliente/inicio", headers=headers)

    nucleo_polizas.respuestas[("GET", "/v1/polizas")] = lambda _: httpx.Response(200, json=[])
    nucleo_siniestros.respuestas[("GET", "/v1/siniestros")] = lambda _: httpx.Response(200, json={"id": "x"})
    with pytest.raises(KeyError):
        client.get("/v1/cliente/inicio", headers=headers)


def test_perfil_lee_y_guarda(client, nucleo_identidad):
    nucleo_identidad.respuestas[("GET", f"/v1/usuarios/{UID}")] = lambda _: httpx.Response(
        200,
        json={"usuario_id": UID, "email": "persona@correo.com", "numero_documento": "1012345678"},
    )
    headers = _auth(client)
    leido = client.get("/v1/cliente/perfil", headers=headers)
    assert leido.status_code == 200
    assert leido.json() == {
        "usuarioId": UID,
        "correo": "persona@correo.com",
        "nombre": "",
        "apellidos": "",
        "documento": "1012345678",
    }

    nucleo_identidad.respuestas[("PATCH", f"/v1/usuarios/{UID}/perfil")] = lambda _: httpx.Response(
        200,
        json={
            "usuario_id": UID,
            "email": "persona@correo.com",
            "nombre": "Camila",
            "apellidos": "Restrepo",
            "numero_documento": "1012345678",
        },
    )
    guardado = client.patch(
        "/v1/cliente/perfil", headers=headers, json={"nombre": "Camila", "apellidos": "Restrepo"}
    )
    assert guardado.status_code == 200
    assert guardado.json()["nombre"] == "Camila"
    assert guardado.json()["apellidos"] == "Restrepo"


def test_token_sin_uid_no_abre_el_canal():
    from fastapi import HTTPException

    from app.routers.cliente import contexto_canonico

    with pytest.raises(HTTPException) as exc:
        contexto_canonico({})
    assert exc.value.status_code == 401


def test_sin_token_es_401(client):
    assert client.get("/v1/cliente/inicio").status_code == 401
