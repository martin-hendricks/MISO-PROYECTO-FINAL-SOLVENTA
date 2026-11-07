from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.domain.modelos import Notificacion
from tests.dobles import sembrar_notificaciones

USUARIO = UUID("11111111-1111-1111-1111-111111111111")
OTRO = UUID("22222222-2222-2222-2222-222222222222")

DISPOSITIVOS = "/v1/notificaciones/dispositivos"
NOTIFICACIONES = "/v1/notificaciones"


def _datos(usuario_id, ahora=None, **cambios):
    datos = {
        "usuario_id": usuario_id,
        "evento_origen_id": uuid4(),
        "canal": "push",
        "tipo": "poliza_emitida",
        "titulo": "Tu póliza está lista",
        "cuerpo": "Ya puedes consultar tu póliza.",
        "ahora": ahora,
    }
    datos.update(cambios)
    return datos


def _registrar_dispositivo(client, token="token-1", plataforma="android"):
    return client.post(DISPOSITIVOS, json={"plataforma": plataforma, "token": token})


def test_registrar_dispositivo_201_y_upsert_200(client):
    primero = _registrar_dispositivo(client)
    reintento = _registrar_dispositivo(client)

    assert primero.status_code == 201
    assert reintento.status_code == 200
    assert reintento.json()["dispositivo_id"] == primero.json()["dispositivo_id"]
    assert primero.json()["usuario_id"] == str(USUARIO)
    assert primero.json()["activo"] is True


def test_registrar_dispositivo_token_vacio_es_422(client):
    respuesta = _registrar_dispositivo(client, token="   ")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "token_vacio"


def test_registrar_dispositivo_plataforma_invalida_es_422(client):
    respuesta = _registrar_dispositivo(client, plataforma="windows")

    assert respuesta.status_code == 422
    assert respuesta.json()["codigo"] == "plataforma_invalida"


def test_desactivar_dispositivo_propio_y_ajeno(client, client_otro):
    creado = _registrar_dispositivo(client).json()

    assert client_otro.delete(f"{DISPOSITIVOS}/{creado['dispositivo_id']}").status_code == 404
    assert client.delete(f"{DISPOSITIVOS}/{creado['dispositivo_id']}").status_code == 204

    reactivado = _registrar_dispositivo(client)
    assert reactivado.status_code == 200
    assert reactivado.json()["dispositivo_id"] == creado["dispositivo_id"]
    assert reactivado.json()["activo"] is True


def test_listar_solo_las_del_llamante_con_orden_y_cursor(client, almacen):
    base = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    propias = [
        Notificacion.crear(**_datos(USUARIO, base + timedelta(minutes=i))) for i in range(3)
    ]
    ajena = Notificacion.crear(**_datos(OTRO, base + timedelta(minutes=10)))
    sembrar_notificaciones(almacen, [*propias, ajena])

    todas = client.get(NOTIFICACIONES).json()
    dos = client.get(NOTIFICACIONES, params={"limite": 2}).json()
    anteriores = client.get(
        NOTIFICACIONES, params={"antes_de": (base + timedelta(minutes=2)).isoformat()}
    ).json()

    assert [n["notificacion_id"] for n in todas] == [
        str(propias[2].notificacion_id),
        str(propias[1].notificacion_id),
        str(propias[0].notificacion_id),
    ]
    assert [n["notificacion_id"] for n in dos] == [
        str(propias[2].notificacion_id),
        str(propias[1].notificacion_id),
    ]
    assert [n["notificacion_id"] for n in anteriores] == [
        str(propias[1].notificacion_id),
        str(propias[0].notificacion_id),
    ]
    assert ajena.notificacion_id not in {UUID(n["notificacion_id"]) for n in todas}


def test_listar_valida_limite(client):
    assert client.get(NOTIFICACIONES, params={"limite": 0}).status_code == 422
    assert client.get(NOTIFICACIONES, params={"limite": 101}).status_code == 422


def test_detalle_propio_y_ajeno(client, client_otro, almacen):
    propia = Notificacion.crear(**_datos(USUARIO))
    ajena = Notificacion.crear(**_datos(OTRO))
    sembrar_notificaciones(almacen, [propia, ajena])

    assert client.get(f"{NOTIFICACIONES}/{propia.notificacion_id}").status_code == 200
    assert client.get(f"{NOTIFICACIONES}/{ajena.notificacion_id}").status_code == 404
    assert client_otro.get(f"{NOTIFICACIONES}/{propia.notificacion_id}").status_code == 404
    assert client.get(f"{NOTIFICACIONES}/{uuid4()}").status_code == 404


def test_marcar_leida_propia_es_idempotente_y_ajena_404(client, almacen):
    propia = Notificacion.crear(**_datos(USUARIO))
    ajena = Notificacion.crear(**_datos(OTRO))
    sembrar_notificaciones(almacen, [propia, ajena])

    primera = client.post(f"{NOTIFICACIONES}/{propia.notificacion_id}/leida")
    segunda = client.post(f"{NOTIFICACIONES}/{propia.notificacion_id}/leida")

    assert primera.status_code == 200
    assert segunda.status_code == 200
    assert primera.json()["estado"] == "leida"
    assert segunda.json()["leida_en"] == primera.json()["leida_en"]
    assert client.post(f"{NOTIFICACIONES}/{ajena.notificacion_id}/leida").status_code == 404


def test_sin_token_es_401(client):
    assert client.request("GET", NOTIFICACIONES, sin_token=True).status_code == 401
    assert (
        client.request("GET", f"{NOTIFICACIONES}/{uuid4()}", sin_token=True).status_code == 401
    )
    assert (
        client.request(
            "POST",
            DISPOSITIVOS,
            json={"plataforma": "android", "token": "token-1"},
            sin_token=True,
        ).status_code
        == 401
    )


def test_token_ajeno_no_ve_datos(client, client_otro, almacen):
    propia = Notificacion.crear(**_datos(USUARIO))
    sembrar_notificaciones(almacen, [propia])

    assert client_otro.get(NOTIFICACIONES).json() == []
    assert client_otro.get(f"{NOTIFICACIONES}/{propia.notificacion_id}").status_code == 404


def test_health_metrics_y_correlacion(client):
    salud = client.get("/health", headers={"X-Correlation-Id": "c-123"})

    assert salud.json() == {"status": "ok"}
    assert salud.headers["X-Correlation-Id"] == "c-123"
    assert "http_request_duration_seconds" in client.get("/metrics").text
