import json
from uuid import uuid4

from app.config import Settings
from app.domain.modelos import DispositivoPush
from app.infrastructure.kafka_consumer import ConsumidorMSK, MSKTokenProvider
from tests.dobles import PushDoble


def _config(**cambios) -> Settings:
    datos = {
        "msk_bootstrap_brokers": "b-1.solventa.kafka.us-east-1.amazonaws.com:9098",
        "msk_topic": "BusEventos",
        "msk_consumer_group": "notificaciones",
    }
    datos.update(cambios)
    return Settings(**datos)


def _mensaje(usuario_id, **extras):
    payload = {"usuario_id": str(usuario_id), "numero": "POL-1", "fin_vigencia": "2027-01-01"}
    payload.update(extras)
    return {
        "evento_id": str(uuid4()),
        "tipo": "PolizaEmitida",
        "agregado_id": str(uuid4()),
        "ocurrido_en": "2026-11-06T12:00:00+00:00",
        "origen": "ms_polizas",
        "payload": payload,
    }


async def test_procesar_mensaje_valido_crea_y_despacha(uow, almacen, push):
    usuario = uuid4()
    dispositivo = DispositivoPush.registrar(usuario, "ios", "token-1")
    almacen.dispositivos[dispositivo.dispositivo_id] = dispositivo
    consumidor = ConsumidorMSK(_config(), uow, push)

    notificacion = await consumidor.procesar_mensaje(json.dumps(_mensaje(usuario)).encode("utf-8"))

    assert notificacion is not None
    assert notificacion.usuario_id == usuario
    assert notificacion.estado == "enviada"
    assert almacen.notificaciones[notificacion.notificacion_id].estado == "enviada"
    assert len(push.llamadas) == 1


async def test_procesar_mensaje_corrupto_no_lanza_y_devuelve_none(uow, almacen):
    consumidor = ConsumidorMSK(_config(), uow, PushDoble())

    assert await consumidor.procesar_mensaje(b"{esto no es json") is None
    assert await consumidor.procesar_mensaje(json.dumps(["lista"])) is None
    assert await consumidor.procesar_mensaje(json.dumps({"evento_id": str(uuid4())})) is None
    assert almacen.notificaciones == {}


async def test_procesar_mensaje_sin_usuario_no_crea_nada(uow, almacen, push):
    consumidor = ConsumidorMSK(_config(), uow, push)
    mensaje = _mensaje(uuid4())
    mensaje["payload"].pop("usuario_id")

    assert await consumidor.procesar_mensaje(mensaje) is None
    assert almacen.notificaciones == {}


async def test_detener_sin_iniciar_no_lanza(uow):
    consumidor = ConsumidorMSK(_config(), uow, PushDoble())

    await consumidor.detener()
    await consumidor.detener()


async def test_detener_es_idempotente_tras_iniciar_sin_brokers(uow, monkeypatch):
    # No se llama a `iniciar()`: solo comprobamos que el estado inicial es seguro.
    consumidor = ConsumidorMSK(_config(), uow, PushDoble())
    assert consumidor._consumer is None and consumidor._tarea is None

    await consumidor.detener()

    assert consumidor._consumer is None and consumidor._tarea is None


def test_provider_de_tokens_usa_la_region_configurada(uow):
    provider = MSKTokenProvider("us-east-1")
    assert provider._region == "us-east-1"


def test_region_por_defecto_cae_a_us_east_1(uow, monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    consumidor = ConsumidorMSK(_config(aws_region=""), uow, PushDoble())

    assert consumidor._region == "us-east-1"


def test_region_toma_la_variable_de_entorno_si_no_hay_config(uow, monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    consumidor = ConsumidorMSK(_config(aws_region=""), uow, PushDoble())

    assert consumidor._region == "us-west-2"
