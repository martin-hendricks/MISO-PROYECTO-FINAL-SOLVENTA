"""API del siniestro asistido (HU-157): multipart, cola del operador, decisión y pago."""

import json
from datetime import date, timedelta
from uuid import uuid4

from .conftest import cabecera

HOY = date.today()
PNG = ("dano.png", b"\x89PNG-contenido", "image/png")


def datos(ramo="proteccion-dispositivo", usuario_id=None, poliza_id=None, **extra):
    cuerpo = {
        "usuario_id": str(usuario_id or uuid4()),
        "canal": "web",
        "poliza": {
            "poliza_id": str(poliza_id or uuid4()),
            "numero": "POL-88421",
            "ramo": ramo,
            "estado": "vigente",
            "inicio_vigencia": str(HOY - timedelta(days=60)),
            "fin_vigencia": str(HOY + timedelta(days=300)),
            "suma_asegurada": "5000000",
        },
        "fecha_hecho": str(HOY - timedelta(days=1)),
        "descripcion": "Pantalla rota",
        "geo": {"lat": "4.6533", "lng": "-74.0836", "precision_m": "12"},
        "tipos_adjuntos": ["foto"],
    }
    return json.dumps(cuerpo | extra)


def avisar(client, archivos=(PNG,), cabeceras=None, usuario_id=None, **kw):
    """Avisa como el cliente dueño: el token lleva el mismo uid que el cuerpo."""
    usuario_id = usuario_id or uuid4()
    return client.post(
        "/v1/siniestros",
        data={"datos": datos(usuario_id=usuario_id, **kw)},
        files=[("archivos", a) for a in archivos],
        headers={**cabecera("cliente", usuario_id), **(cabeceras or {})},
    )


def test_post_aviso_201_recibido_con_evidencia_y_url_firmada(client, almacen_evidencias):
    r = avisar(client)

    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["siniestro"]["estado"] == "recibido"
    assert cuerpo["siniestro"]["tipo"] == "asistido"
    assert cuerpo["siniestro"]["numero"].startswith("SIN-")
    assert cuerpo["siniestro"]["geo"]["lat"] == "4.653300"
    adjunto = cuerpo["adjuntos"][0]
    assert adjunto["tipo"] == "foto"
    assert adjunto["url"].startswith("memoria://")
    assert len(almacen_evidencias.objetos) == 1


def test_post_aviso_guarda_el_lugar_y_omite_el_vacio(client):
    con_lugar = avisar(client, lugar="Calle 72")
    assert con_lugar.status_code == 201, con_lugar.text
    assert con_lugar.json()["siniestro"]["lugar"] == "Calle 72"
    sin_lugar = avisar(client, lugar="   ")
    assert sin_lugar.status_code == 201
    assert sin_lugar.json()["siniestro"]["lugar"] is None


def test_post_aviso_sin_archivo_sigue_rechazado(client):
    r = avisar(client, archivos=())
    assert r.status_code == 422


def test_post_aviso_sin_geo_sigue(client):
    r = avisar(client, geo=None)
    assert r.status_code == 201
    assert r.json()["siniestro"]["geo"] is None


def test_post_aviso_reintento_con_idempotency_key_200_mismo_siniestro(client):
    a = avisar(client, cabeceras={"Idempotency-Key": "k-1"})
    b = avisar(client, cabeceras={"Idempotency-Key": "k-1"})
    assert (a.status_code, b.status_code) == (201, 200)
    assert a.json()["siniestro"]["id"] == b.json()["siniestro"]["id"]


def test_post_aviso_tipo_de_archivo_no_permitido_422(client):
    r = avisar(client, archivos=(("virus.exe", b"MZ", "application/x-msdownload"),))
    assert r.status_code == 422
    assert r.json()["codigo"] == "evidencia_tipo_no_permitido"


def test_post_aviso_datos_invalidos_422(client):
    r = client.post(
        "/v1/siniestros", data={"datos": "{no es json"}, files=[("archivos", PNG)], headers=cabecera("cliente")
    )
    assert r.status_code == 422
    assert r.json()["codigo"] == "aviso_invalido"


def test_post_aviso_s3_caido_503(client, almacen_evidencias):
    almacen_evidencias.fallar = True
    r = avisar(client)
    assert r.status_code == 503
    assert r.json()["codigo"] == "evidencia_no_disponible"


def test_evaluacion_asincrona_y_lista_del_cliente(client):
    usuario = uuid4()
    creado = avisar(client, usuario_id=usuario).json()["siniestro"]["id"]
    avisar(client)  # de otro usuario

    assert client.post("/v1/siniestros/evaluaciones-pendientes").json() == {"procesados": 2}

    mios = client.get("/v1/siniestros", params={"usuario_id": str(usuario)}).json()
    assert [s["id"] for s in mios] == [creado]
    assert mios[0]["estado"] == "pagado"
    assert mios[0]["resultado"] == "aprobado"
    assert float(mios[0]["reserva"]) == 420000


def test_detalle_del_cliente_no_expone_siniestros_ajenos(client):
    usuario = uuid4()
    sid = avisar(client, usuario_id=usuario).json()["siniestro"]["id"]

    assert client.get(f"/v1/siniestros/{sid}/detalle", params={"usuario_id": str(usuario)}).status_code == 200
    assert client.get(f"/v1/siniestros/{sid}/detalle", params={"usuario_id": str(uuid4())}).status_code == 404


def test_cola_del_operador_decision_y_auditoria(client):
    sid = avisar(client, ramo="vida-crediticia").json()["siniestro"]["id"]
    client.post("/v1/siniestros/evaluaciones-pendientes")

    pendientes = client.get(
        "/v1/siniestros", params={"tipo": "asistido", "requiere_revision": "true"}
    ).json()
    assert [s["id"] for s in pendientes] == [sid]

    sin_motivo = client.post(f"/v1/siniestros/{sid}/decision", json={"resultado": "rechazado", "actor": "ana"})
    assert sin_motivo.status_code == 422

    r = client.post(
        f"/v1/siniestros/{sid}/decision",
        json={"resultado": "rechazado", "motivo": "Falta soporte de la factura", "actor": "ana"},
    )
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["siniestro"]["resultado"] == "rechazado"
    assert cuerpo["decisiones"][-1] | {"decidida_en": None} == {
        "origen": "operador",
        "actor": "operador@solventa.co",  # la identidad del token, no la del cuerpo
        "resultado": "rechazado",
        "motivo": "Falta soporte de la factura",
        "reglas": [],
        "decidida_en": None,
    }
    rechazados = client.get("/v1/siniestros", params={"resultado": "rechazado"}).json()
    assert [s["id"] for s in rechazados] == [sid]

    otra_vez = client.post(f"/v1/siniestros/{sid}/decision", json={"resultado": "aprobado", "actor": "luis"})
    assert otra_vez.status_code == 409


def test_enrutar_a_perito(client):
    sid = avisar(client, ramo="vida-crediticia").json()["siniestro"]["id"]
    client.post("/v1/siniestros/evaluaciones-pendientes")

    r = client.post(f"/v1/siniestros/{sid}/perito", json={"motivo": "Inspección", "actor": "ana"})

    assert r.status_code == 200
    assert r.json()["siniestro"]["estado"] == "enrutado"


def test_pago_bajo_monto_201_y_reintento_200_mismo_comprobante(client, adaptador_desembolso):
    poliza = uuid4()
    avisar(client, poliza_id=poliza)
    sid = avisar(client, poliza_id=poliza).json()["siniestro"]["id"]  # duplicado -> revisión
    client.post("/v1/siniestros/evaluaciones-pendientes")
    client.post(f"/v1/siniestros/{sid}/decision", json={"resultado": "aprobado", "actor": "ana"})

    primero = client.post(f"/v1/siniestros/{sid}/pago", json={"actor": "ana"})
    reintento = client.post(f"/v1/siniestros/{sid}/pago", json={"actor": "ana"})

    assert (primero.status_code, reintento.status_code) == (201, 200)
    assert reintento.json()["reintento"] is True
    assert reintento.json()["pago"]["comprobante"] == primero.json()["pago"]["comprobante"]
    intentos = [i["resultado"] for i in reintento.json()["detalle"]["intentos_pago"]]
    assert intentos == ["ejecutado", "reintento_idempotente"]


def test_parametros_de_ramo(client):
    ramos = {p["ramo"]: p for p in client.get("/v1/parametros-ramo").json()}
    assert float(ramos["proteccion-dispositivo"]["umbral_automatico"]) == 500000


def test_lista_sin_filtros_conserva_comportamiento_previo(client):
    client.post(
        "/v1/eventos-parametricos",
        json={"evento_id": "evt-p", "valor": "100", "umbral": "80", "poliza_vigente": True, "monto_pago": "5"},
    )
    avisar(client)
    tipos = sorted(s["tipo"] for s in client.get("/v1/siniestros").json())
    assert tipos == ["asistido", "parametrico"]


def test_solo_el_cliente_dueno_puede_avisar(client):
    usuario = uuid4()
    ajeno = client.post(
        "/v1/siniestros",
        data={"datos": datos(usuario_id=usuario)},
        files=[("archivos", PNG)],
        headers=cabecera("cliente", uuid4()),
    )
    operador = client.post(
        "/v1/siniestros", data={"datos": datos(usuario_id=usuario)}, files=[("archivos", PNG)]
    )
    assert (ajeno.status_code, operador.status_code) == (404, 404)


def test_sin_token_401(client):
    r = client.get("/v1/parametros-ramo", headers={"Authorization": ""})
    assert r.status_code == 401


def test_el_cliente_solo_ve_lo_suyo_aunque_no_filtre(client):
    usuario = uuid4()
    mio = avisar(client, usuario_id=usuario).json()["siniestro"]["id"]
    ajeno = avisar(client).json()["siniestro"]["id"]
    como_cliente = cabecera("cliente", usuario)

    lista = client.get("/v1/siniestros", headers=como_cliente).json()
    assert [s["id"] for s in lista] == [mio]
    assert client.get(f"/v1/siniestros/{mio}/detalle", headers=como_cliente).status_code == 200
    assert client.get(f"/v1/siniestros/{ajeno}/detalle", headers=como_cliente).status_code == 404


def test_acciones_del_operador_prohibidas_al_cliente_y_al_asesor(client):
    sid = avisar(client, ramo="vida-crediticia").json()["siniestro"]["id"]
    for rol in ("cliente", "asesor"):
        h = cabecera(rol)
        assert client.post("/v1/siniestros/evaluaciones-pendientes", headers=h).status_code == 403
        assert (
            client.post(f"/v1/siniestros/{sid}/decision", json={"resultado": "aprobado", "actor": "x"}, headers=h)
        ).status_code == 403
        assert client.post(f"/v1/siniestros/{sid}/perito", json={"motivo": "m", "actor": "x"}, headers=h).status_code == 403
        assert client.post(f"/v1/siniestros/{sid}/pago", json={"actor": "x"}, headers=h).status_code == 403
