import json
from uuid import uuid4

from app.config import Settings
from app.infrastructure.kafka_consumer import ConsumidorMSK, MSKTokenProvider


def _config(**cambios) -> Settings:
    datos = {
        "msk_bootstrap_brokers": "b-1.solventa.kafka.us-east-1.amazonaws.com:9098",
        "msk_topic": "BusEventos",
        "msk_consumer_group": "analitica-cg",
    }
    datos.update(cambios)
    return Settings(**datos)


def _mensaje(**extras):
    datos = {
        "evento_id": str(uuid4()),
        "tipo": "PolizaEmitida",
        "agregado_id": str(uuid4()),
        "ocurrido_en": "2026-03-01T00:00:00+00:00",
        "origen": "ms_polizas",
        "payload": {"usuario_id": str(uuid4())},
    }
    datos.update(extras)
    return datos


async def test_procesar_mensaje_valido_incrementa(uow, almacen):
    consumidor = ConsumidorMSK(_config(), uow)

    resultado = await consumidor.procesar_mensaje(json.dumps(_mensaje()).encode("utf-8"))

    assert resultado is True
    assert sum(almacen.conteos.values()) == 1


async def test_procesar_mensaje_corrupto_no_lanza_y_devuelve_false(uow, almacen):
    consumidor = ConsumidorMSK(_config(), uow)

    assert await consumidor.procesar_mensaje(b"{esto no es json") is False
    assert await consumidor.procesar_mensaje(json.dumps(["lista"])) is False
    assert await consumidor.procesar_mensaje(json.dumps({"evento_id": str(uuid4())})) is False
    assert not almacen.conteos


async def test_procesar_mensaje_tipo_desconocido_no_incrementa(uow, almacen):
    consumidor = ConsumidorMSK(_config(), uow)

    resultado = await consumidor.procesar_mensaje(json.dumps(_mensaje(tipo="Otro")).encode())

    assert resultado is False
    assert not almacen.conteos


async def test_detener_sin_iniciar_no_lanza(uow):
    consumidor = ConsumidorMSK(_config(), uow)

    await consumidor.detener()
    await consumidor.detener()


async def test_detener_es_idempotente_tras_iniciar_sin_brokers(uow):
    consumidor = ConsumidorMSK(_config(), uow)
    assert consumidor._consumer is None and consumidor._tarea is None

    await consumidor.detener()

    assert consumidor._consumer is None and consumidor._tarea is None


def test_provider_de_tokens_usa_la_region_configurada():
    provider = MSKTokenProvider("us-east-1")
    assert provider._region == "us-east-1"


def test_region_por_defecto_cae_a_us_east_1(uow, monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    consumidor = ConsumidorMSK(_config(aws_region=""), uow)
    assert consumidor._region == "us-east-1"


def test_region_usa_la_configurada_explicitamente(uow):
    consumidor = ConsumidorMSK(_config(aws_region="eu-west-1"), uow)
    assert consumidor._region == "eu-west-1"
