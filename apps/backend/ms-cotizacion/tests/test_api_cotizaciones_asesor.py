"""HU-163 (SOLV-262): cotizaciones pendientes del asesor (GET /v1/cotizaciones)."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.modelos import EstadoSolicitud

from .test_api_cotizaciones import _payload


def _crear(client, almacen, asesor_id, *, minutos_atras=0, cliente_ref="CC-123"):
    """Crea una cotización por HTTP y fija su creada_en para que el orden sea determinista."""
    payload = _payload()
    if asesor_id is not None:
        payload["asesor_id"] = str(asesor_id)
        payload["cliente_ref"] = cliente_ref
    respuesta = client.post("/v1/cotizaciones", json=payload, headers={"Idempotency-Key": f"clave-{uuid4()}"})
    assert respuesta.status_code == 201
    cotizacion_id = respuesta.json()["cotizacion_id"]
    solicitud = next(s for s in almacen.solicitudes.values() if str(s.id) == cotizacion_id)
    solicitud.creada_en = datetime.now(UTC) - timedelta(minutes=minutos_atras)
    return solicitud


def _vencer(almacen, solicitud):
    oferta = next(o for o in almacen.ofertas.values() if o.solicitud_id == solicitud.id)
    oferta.vence_en = datetime.now(UTC) - timedelta(seconds=1)
    return oferta


def _ids(cuerpo):
    return [item["cotizacion_id"] for item in cuerpo["items"]]


def test_lista_solo_las_cotizaciones_del_asesor(client, almacen):
    asesor = uuid4()
    propia = _crear(client, almacen, asesor)
    _crear(client, almacen, uuid4())
    _crear(client, almacen, None)

    respuesta = client.get("/v1/cotizaciones", params={"asesor_id": str(asesor)})

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert _ids(cuerpo) == [str(propia.id)]
    item = cuerpo["items"][0]
    oferta = next(o for o in almacen.ofertas.values() if o.solicitud_id == propia.id)
    assert item["oferta_id"] == str(oferta.id)
    assert item["cliente_ref"] == "CC-123"
    assert item["estado"] == "cotizada"
    assert item["vencida"] is False
    assert {"producto", "prima", "moneda", "creada_en", "vence_en"} <= set(item)
    assert cuerpo["pagina"] == 1 and cuerpo["tamano"] == 20 and cuerpo["hay_mas"] is False


def test_excluye_rechazadas_y_recibidas_e_incluye_aceptadas(client, almacen):
    asesor = uuid4()
    cotizada = _crear(client, almacen, asesor, minutos_atras=1)
    aceptada = _crear(client, almacen, asesor, minutos_atras=2)
    aceptada.estado = EstadoSolicitud.ACEPTADA
    _crear(client, almacen, asesor, minutos_atras=3).estado = EstadoSolicitud.RECHAZADA
    _crear(client, almacen, asesor, minutos_atras=4).estado = EstadoSolicitud.RECIBIDA

    cuerpo = client.get("/v1/cotizaciones", params={"asesor_id": str(asesor)}).json()

    assert _ids(cuerpo) == [str(cotizada.id), str(aceptada.id)]


def test_filtra_por_estados_explicitos(client, almacen):
    asesor = uuid4()
    _crear(client, almacen, asesor, minutos_atras=1)
    aceptada = _crear(client, almacen, asesor, minutos_atras=2)
    aceptada.estado = EstadoSolicitud.ACEPTADA

    cuerpo = client.get("/v1/cotizaciones", params={"asesor_id": str(asesor), "estados": "aceptada"}).json()

    assert _ids(cuerpo) == [str(aceptada.id)]


def test_oculta_vencidas_por_defecto(client, almacen):
    asesor = uuid4()
    vigente = _crear(client, almacen, asesor, minutos_atras=1)
    _vencer(almacen, _crear(client, almacen, asesor, minutos_atras=2))

    cuerpo = client.get("/v1/cotizaciones", params={"asesor_id": str(asesor)}).json()

    assert _ids(cuerpo) == [str(vigente.id)]


def test_incluir_vencidas_las_lista_y_las_marca(client, almacen):
    asesor = uuid4()
    vigente = _crear(client, almacen, asesor, minutos_atras=1)
    vencida = _crear(client, almacen, asesor, minutos_atras=2)
    _vencer(almacen, vencida)

    cuerpo = client.get(
        "/v1/cotizaciones", params={"asesor_id": str(asesor), "incluir_vencidas": "true"}
    ).json()

    assert _ids(cuerpo) == [str(vigente.id), str(vencida.id)]
    assert [item["vencida"] for item in cuerpo["items"]] == [False, True]


def test_ordena_por_creada_en_descendente(client, almacen):
    asesor = uuid4()
    vieja = _crear(client, almacen, asesor, minutos_atras=30)
    nueva = _crear(client, almacen, asesor, minutos_atras=1)
    media = _crear(client, almacen, asesor, minutos_atras=10)

    cuerpo = client.get("/v1/cotizaciones", params={"asesor_id": str(asesor)}).json()

    assert _ids(cuerpo) == [str(nueva.id), str(media.id), str(vieja.id)]


def test_pagina_con_hay_mas(client, almacen):
    asesor = uuid4()
    creadas = [_crear(client, almacen, asesor, minutos_atras=i) for i in range(3)]

    primera = client.get("/v1/cotizaciones", params={"asesor_id": str(asesor), "tamano": 2}).json()
    segunda = client.get(
        "/v1/cotizaciones", params={"asesor_id": str(asesor), "tamano": 2, "pagina": 2}
    ).json()

    assert _ids(primera) == [str(creadas[0].id), str(creadas[1].id)]
    assert primera["hay_mas"] is True and primera["pagina"] == 1 and primera["tamano"] == 2
    assert _ids(segunda) == [str(creadas[2].id)]
    assert segunda["hay_mas"] is False and segunda["pagina"] == 2


def test_sin_pendientes_devuelve_lista_vacia(client):
    respuesta = client.get("/v1/cotizaciones", params={"asesor_id": str(uuid4())})

    assert respuesta.status_code == 200
    assert respuesta.json() == {"items": [], "pagina": 1, "tamano": 20, "hay_mas": False}


def test_sin_asesor_id_devuelve_422(client):
    assert client.get("/v1/cotizaciones").status_code == 422


def test_limites_de_paginacion_devuelven_422(client):
    asesor = str(uuid4())
    for params in ({"tamano": 0}, {"tamano": 101}, {"pagina": 0}):
        respuesta = client.get("/v1/cotizaciones", params={"asesor_id": asesor, **params})
        assert respuesta.status_code == 422, params
    assert client.get("/v1/cotizaciones", params={"asesor_id": asesor, "tamano": 100}).status_code == 200


def test_estado_desconocido_devuelve_422(client):
    respuesta = client.get("/v1/cotizaciones", params={"asesor_id": str(uuid4()), "estados": "cotizada,emitida"})

    assert respuesta.status_code == 422


def test_cliente_ref_mayor_a_100_devuelve_422(client):
    payload = _payload(asesor_id=str(uuid4()), cliente_ref="x" * 101)

    respuesta = client.post("/v1/cotizaciones", json=payload, headers={"Idempotency-Key": "clave-larga-0001"})

    assert respuesta.status_code == 422


def test_post_sin_asesor_conserva_la_respuesta_y_no_guarda_asesor(client, almacen):
    respuesta = client.post("/v1/cotizaciones", json=_payload(), headers={"Idempotency-Key": "clave-sin-asesor"})

    assert respuesta.status_code == 201
    assert set(respuesta.json()) == {
        "cotizacion_id", "estado", "producto", "creada_en", "prima", "prima_neta",
        "gastos_expedicion", "moneda", "vence_en", "factor_riesgo_origen", "vencida",
    }
    solicitud = next(iter(almacen.solicitudes.values()))
    assert solicitud.asesor_id is None and solicitud.cliente_ref is None


def test_reintento_idempotente_con_asesor_devuelve_la_misma_cotizacion(client, almacen):
    asesor = uuid4()
    payload = _payload(asesor_id=str(asesor), cliente_ref="CC-9")
    cabeceras = {"Idempotency-Key": "clave-asesor-0001"}

    primera = client.post("/v1/cotizaciones", json=payload, headers=cabeceras)
    segunda = client.post("/v1/cotizaciones", json=payload, headers=cabeceras)

    assert (primera.status_code, segunda.status_code) == (201, 200)
    assert primera.json()["cotizacion_id"] == segunda.json()["cotizacion_id"]
    assert len(almacen.solicitudes) == 1
    solicitud = next(iter(almacen.solicitudes.values()))
    assert (solicitud.asesor_id, solicitud.cliente_ref) == (asesor, "CC-9")
