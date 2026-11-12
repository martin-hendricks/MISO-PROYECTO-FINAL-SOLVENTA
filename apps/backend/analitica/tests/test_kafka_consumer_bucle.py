"""Cubre iniciar()/_bucle()/detener() con un AIOKafkaConsumer falso -- sin
broker real. Mismo patrón que test_kafka_consumer.py, pero ejercitando el
ciclo de vida completo en vez de solo procesar_mensaje()."""

import asyncio
import inspect
import json
import ssl
from uuid import uuid4

import pytest

from app.config import Settings
from app.infrastructure import kafka_consumer as kafka_consumer_module
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


class _Mensaje:
    def __init__(self, value, topic="BusEventos", offset=1):
        self.value = value
        self.topic = topic
        self.offset = offset


class _ConsumerFalso:
    instancias: list["_ConsumerFalso"] = []

    def __init__(self, *topics, **kwargs):
        self.topics = topics
        self.kwargs = kwargs
        self.started = False
        self.stopped = False
        self._mensajes: list[_Mensaje] = []
        # Señal real de sincronización: se activa justo antes de bloquear a
        # esperar el próximo mensaje, es decir, una vez que _bucle ya
        # terminó de procesar el mensaje anterior y volvió a pedir el
        # siguiente -- el test espera esta señal en vez de dormir un
        # tiempo fijo y no determinista.
        self.ciclo_completo = asyncio.Event()
        _ConsumerFalso.instancias.append(self)

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._mensajes:
            return self._mensajes.pop(0)
        self.ciclo_completo.set()
        # Simula el bloqueo real de un consumer esperando el próximo mensaje
        # del tópico -- se queda esperando indefinidamente hasta que la
        # tarea se cancela desde afuera (detener()).
        await asyncio.Event().wait()
        raise AssertionError("no debería llegar aquí en un test")


@pytest.fixture(autouse=True)
def _limpiar_instancias():
    _ConsumerFalso.instancias.clear()
    yield
    _ConsumerFalso.instancias.clear()


@pytest.fixture
def consumer_falso(monkeypatch):
    import aiokafka

    monkeypatch.setattr(aiokafka, "AIOKafkaConsumer", _ConsumerFalso)
    return _ConsumerFalso


async def test_iniciar_arranca_el_consumer_y_la_tarea(uow, consumer_falso):
    consumidor = ConsumidorMSK(_config(), uow)

    await consumidor.iniciar()

    assert consumidor._consumer is not None
    assert consumidor._consumer.started is True
    assert consumidor._tarea is not None
    assert not consumidor._tarea.done()

    await consumidor.detener()


async def test_iniciar_pasa_un_contexto_tls_explicito(uow, consumer_falso):
    # aiokafka >= 0.13 exige el contexto TLS para SASL_SSL: sin él el
    # constructor lanza ValueError antes de conectar (ver kafka_consumer.py
    # de notificaciones, donde el fallo se vio en el clúster real).
    consumidor = ConsumidorMSK(_config(), uow)

    await consumidor.iniciar()

    contexto = consumer_falso.instancias[0].kwargs["ssl_context"]
    assert isinstance(contexto, ssl.SSLContext)
    assert contexto.verify_mode == ssl.CERT_REQUIRED

    await consumidor.detener()


async def test_iniciar_es_idempotente_si_ya_hay_consumer(uow, consumer_falso):
    consumidor = ConsumidorMSK(_config(), uow)
    await consumidor.iniciar()
    primero = consumidor._consumer

    await consumidor.iniciar()

    assert consumidor._consumer is primero
    assert len(consumer_falso.instancias) == 1

    await consumidor.detener()


async def test_bucle_procesa_un_mensaje_real_del_consumer(uow, almacen, consumer_falso):
    consumidor = ConsumidorMSK(_config(), uow)
    await consumidor.iniciar()
    consumidor._consumer._mensajes.append(_Mensaje(json.dumps(_mensaje()).encode("utf-8")))

    await asyncio.wait_for(consumidor._consumer.ciclo_completo.wait(), timeout=1)

    assert sum(almacen.conteos.values()) == 1
    await consumidor.detener()


async def test_bucle_ignora_mensaje_cuyo_payload_no_es_un_objeto(uow, almacen, consumer_falso):
    mensaje = _mensaje(payload="no soy un objeto")
    consumidor = ConsumidorMSK(_config(), uow)
    await consumidor.iniciar()
    consumidor._consumer._mensajes.append(_Mensaje(json.dumps(mensaje).encode()))

    await asyncio.wait_for(consumidor._consumer.ciclo_completo.wait(), timeout=1)

    assert not almacen.conteos
    await consumidor.detener()


async def test_bucle_captura_json_invalido_por_la_rama_except(uow, almacen, consumer_falso):
    consumidor = ConsumidorMSK(_config(), uow)
    await consumidor.iniciar()
    consumidor._consumer._mensajes.append(_Mensaje(b"{esto no es json"))

    await asyncio.wait_for(consumidor._consumer.ciclo_completo.wait(), timeout=1)

    assert not almacen.conteos
    assert not consumidor._tarea.done()
    await consumidor.detener()


async def test_bucle_captura_excepcion_de_manejar_evento_y_sigue(
    uow, almacen, consumer_falso, monkeypatch
):
    async def _manejar_que_lanza(*args, **kwargs):
        raise RuntimeError("fallo inesperado procesando el evento")

    monkeypatch.setattr(kafka_consumer_module, "manejar_evento", _manejar_que_lanza)

    consumidor = ConsumidorMSK(_config(), uow)
    await consumidor.iniciar()
    consumidor._consumer._mensajes.append(_Mensaje(json.dumps(_mensaje()).encode()))

    await asyncio.wait_for(consumidor._consumer.ciclo_completo.wait(), timeout=1)

    assert not consumidor._tarea.done()
    await consumidor.detener()


async def test_detener_no_lanza_si_stop_falla(uow, consumer_falso):
    consumidor = ConsumidorMSK(_config(), uow)
    await consumidor.iniciar()

    async def _stop_que_falla():
        raise RuntimeError("fallo simulado al detener")

    consumidor._consumer.stop = _stop_que_falla

    await consumidor.detener()  # no debe lanzar

    assert consumidor._consumer is None


async def test_token_usa_el_firmador_iam(monkeypatch):
    import sys
    import types

    modulo_falso = types.ModuleType("aws_msk_iam_sasl_signer")

    class _Provider:
        @staticmethod
        def generate_auth_token(region):
            return f"token-para-{region}", 0

    modulo_falso.MSKAuthTokenProvider = _Provider
    monkeypatch.setitem(sys.modules, "aws_msk_iam_sasl_signer", modulo_falso)

    provider = MSKTokenProvider("us-east-1")

    assert await provider.token() == "token-para-us-east-1"


def test_provider_cumple_el_contrato_de_aiokafka():
    # aiokafka 0.15 valida isinstance(..., AbstractTokenProvider) al conectar y
    # consume token() con await (ver kafka_consumer.py de notificaciones).
    from aiokafka.abc import AbstractTokenProvider

    provider = MSKTokenProvider("us-east-1")

    assert isinstance(provider, AbstractTokenProvider)
    assert inspect.iscoroutinefunction(provider.token)
