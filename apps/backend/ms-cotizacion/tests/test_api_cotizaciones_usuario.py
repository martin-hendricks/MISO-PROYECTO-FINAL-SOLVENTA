"""Cotizaciones pendientes del usuario (GET /v1/cotizaciones/por-usuario/{usuario_id})."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

from app.domain.modelos import EstadoSolicitud

from .test_api_cotizaciones import _payload
from .test_api_cotizaciones_asesor import _ids, _vencer


def _crear(client, almacen, usuario_id, *, minutos_atras=0):
    payload = _payload(usuario_id=str(usuario_id))
    respuesta = client.post("/v1/cotizaciones", json=payload, headers={"Idempotency-Key": f"clave-{uuid4()}"})
    assert respuesta.status_code == 201
    cotizacion_id = respuesta.json()["cotizacion_id"]
    solicitud = next(s for s in almacen.solicitudes.values() if str(s.id) == cotizacion_id)
    solicitud.creada_en = datetime.now(UTC) - timedelta(minutes=minutos_atras)
    return solicitud


def test_lista_solo_las_cotizadas_vigentes_del_usuario(client, almacen):
    usuario = uuid4()
    propia = _crear(client, almacen, usuario, minutos_atras=1)
    _crear(client, almacen, uuid4())
    aceptada = _crear(client, almacen, usuario, minutos_atras=2)
    aceptada.estado = EstadoSolicitud.ACEPTADA
    _vencer(almacen, _crear(client, almacen, usuario, minutos_atras=3))

    respuesta = client.get(f"/v1/cotizaciones/por-usuario/{usuario}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert _ids(cuerpo) == [str(propia.id)]
    item = cuerpo["items"][0]
    assert item["estado"] == "cotizada"
    assert item["vencida"] is False
    assert "oferta_id" not in item and "cliente_ref" not in item
    assert {"producto", "prima", "moneda", "creada_en", "vence_en"} <= set(item)
    assert cuerpo["pagina"] == 1 and cuerpo["tamano"] == 20 and cuerpo["hay_mas"] is False


def test_ordena_por_creada_en_descendente(client, almacen):
    usuario = uuid4()
    vieja = _crear(client, almacen, usuario, minutos_atras=30)
    nueva = _crear(client, almacen, usuario, minutos_atras=1)

    cuerpo = client.get(f"/v1/cotizaciones/por-usuario/{usuario}").json()

    assert _ids(cuerpo) == [str(nueva.id), str(vieja.id)]


def test_pagina_con_hay_mas(client, almacen):
    usuario = uuid4()
    creadas = [_crear(client, almacen, usuario, minutos_atras=i) for i in range(3)]

    primera = client.get(f"/v1/cotizaciones/por-usuario/{usuario}", params={"tamano": 2}).json()
    segunda = client.get(
        f"/v1/cotizaciones/por-usuario/{usuario}", params={"tamano": 2, "pagina": 2}
    ).json()

    assert _ids(primera) == [str(creadas[0].id), str(creadas[1].id)]
    assert primera["hay_mas"] is True
    assert _ids(segunda) == [str(creadas[2].id)]
    assert segunda["hay_mas"] is False


def test_sin_pendientes_devuelve_lista_vacia(client):
    respuesta = client.get(f"/v1/cotizaciones/por-usuario/{uuid4()}")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"items": [], "pagina": 1, "tamano": 20, "hay_mas": False}


def test_limites_de_paginacion_devuelven_422(client):
    usuario = str(uuid4())
    for params in ({"tamano": 0}, {"tamano": 101}, {"pagina": 0}):
        respuesta = client.get(f"/v1/cotizaciones/por-usuario/{usuario}", params=params)
        assert respuesta.status_code == 422, params
    assert client.get(f"/v1/cotizaciones/por-usuario/{usuario}", params={"tamano": 100}).status_code == 200
