"""Cubre iniciar()/_bucle()/detener() con un AIOKafkaConsumer falso -- sin
broker real. Mismo patrón que test_kafka_consumer.py, pero ejercitando el
ciclo de vida completo en vez de solo procesar_mensaje()."""

import asyncio
import json
import ssl
from uuid import uuid4

import pytest

from app.config import Settings
from app.infrastructure import kafka_consumer as kafka_consumer_module
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


class _Mensaje:
    def __init__(self, value, topic="BusEventos", offset=1):
        self.value = value
        self.topic = topic
        self.offset = offset


class _ConsumerFalso:
    """Doble de AIOKafkaConsumer: start/stop no tocan la red, __aiter__
    entrega mensajes pre-cargados y luego se queda esperando (como un
    consumer real) hasta que la tarea se cancela."""

    instancias: list["_ConsumerFalso"] = []

    def __init__(self, *topics, **kwargs):
        self.topics = topics
        self.kwargs = kwargs
        self.started = False
        self.stopped = False
        self.fallar_en_stop = False
        self._mensajes: list[_Mensaje] = []
        # Señal real de sincronización: se activa justo antes de bloquear a
        # esperar el próximo mensaje, es decir, una vez que _bucle ya
        # terminó de procesar el mensaje anterior (manejar_evento incluido)
        # y volvió a pedir el siguiente -- el test espera esta señal en vez
        # de dormir un tiempo fijo y no determinista.
        self.ciclo_completo = asyncio.Event()
        _ConsumerFalso.instancias.append(self)

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True
        if self.fallar_en_stop:
            raise RuntimeError("fallo simulado al detener")

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._mensajes:
            return self._mensajes.pop(0)
        self.ciclo_completo.set()
        # Simula el bloqueo real de un consumer esperando el próximo mensaje
        # del tópico -- se queda esperando indefinidamente hasta que la
        # tarea se cancela desde afuera (detener()). Un Event que nunca se
        # activa bloquea igual que dormir un tiempo largo, pero sin un
        # tiempo fijo (y sin la cadena que el gate de CI prohíbe en tests
        # unitarios).
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
    consumidor = ConsumidorMSK(_config(), uow, PushDoble())

    await consumidor.iniciar()

    assert consumidor._consumer is not None
    assert consumidor._consumer.started is True
    assert consumidor._tarea is not None
    assert not consumidor._tarea.done()

    await consumidor.detener()


async def test_iniciar_pasa_un_contexto_tls_explicito(uow, consumer_falso):
    # aiokafka >= 0.13 aborta en el constructor cuando security_protocol es
    # SASL_SSL y ssl_context queda en None. El fallo no se veía en los tests
    # (el doble no valida kwargs) ni en el clúster mientras el broker estaba
    # vacío: solo apareció al desplegar con brokers reales.
    consumidor = ConsumidorMSK(_config(), uow, PushDoble())

    await consumidor.iniciar()

    contexto = consumer_falso.instancias[0].kwargs["ssl_context"]
    assert isinstance(contexto, ssl.SSLContext)
    assert contexto.verify_mode == ssl.CERT_REQUIRED

    await consumidor.detener()


async def test_iniciar_es_idempotente_si_ya_hay_consumer(uow, consumer_falso):
    consumidor = ConsumidorMSK(_config(), uow, PushDoble())
    await consumidor.iniciar()
    primero = consumidor._consumer

    await consumidor.iniciar()

    assert consumidor._consumer is primero
    assert len(consumer_falso.instancias) == 1

    await consumidor.detener()


async def test_bucle_procesa_un_mensaje_real_del_consumer(uow, almacen, push, consumer_falso):
    usuario = uuid4()
    from app.domain.modelos import DispositivoPush

    dispositivo = DispositivoPush.registrar(usuario, "ios", "token-1")
    almacen.dispositivos[dispositivo.dispositivo_id] = dispositivo

    mensaje = {
        "evento_id": str(uuid4()),
        "tipo": "PolizaEmitida",
        "agregado_id": str(uuid4()),
        "ocurrido_en": "2026-11-06T12:00:00+00:00",
        "origen": "ms_polizas",
        "payload": {"usuario_id": str(usuario), "numero": "POL-1", "fin_vigencia": "2027-01-01"},
    }

    consumidor = ConsumidorMSK(_config(), uow, push)
    await consumidor.iniciar()
    consumidor._consumer._mensajes.append(
        _Mensaje(json.dumps(mensaje).encode("utf-8"))
    )

    await asyncio.wait_for(consumidor._consumer.ciclo_completo.wait(), timeout=1)

    assert len(almacen.notificaciones) == 1
    assert len(push.llamadas) == 1

    await consumidor.detener()


async def test_bucle_ignora_mensaje_cuyo_payload_no_es_un_objeto(uow, almacen, push, consumer_falso):
    # EventoBus.desde_mensaje devuelve None (no lanza) cuando el JSON es
    # válido y trae los campos obligatorios pero `payload` no es un dict --
    # ejercita la rama "mensaje_msk_ignorado" de _bucle (evento is None),
    # distinta del except genérico (JSON inválido/campos faltantes).
    mensaje = {
        "evento_id": str(uuid4()),
        "tipo": "PolizaEmitida",
        "agregado_id": str(uuid4()),
        "payload": "no soy un objeto",
    }
    consumidor = ConsumidorMSK(_config(), uow, push)
    await consumidor.iniciar()
    consumidor._consumer._mensajes.append(_Mensaje(json.dumps(mensaje).encode()))

    await asyncio.wait_for(consumidor._consumer.ciclo_completo.wait(), timeout=1)

    assert almacen.notificaciones == {}
    await consumidor.detener()


async def test_bucle_captura_json_invalido_por_la_rama_except(uow, almacen, push, consumer_falso):
    consumidor = ConsumidorMSK(_config(), uow, push)
    await consumidor.iniciar()
    consumidor._consumer._mensajes.append(_Mensaje(b"{esto no es json"))

    await asyncio.wait_for(consumidor._consumer.ciclo_completo.wait(), timeout=1)

    assert almacen.notificaciones == {}
    assert not consumidor._tarea.done()
    await consumidor.detener()


async def test_bucle_captura_excepcion_de_manejar_evento_y_sigue(
    uow, almacen, push, consumer_falso, monkeypatch
):
    """Un fallo procesando un mensaje no debe tumbar la tarea de fondo."""
    usuario = uuid4()
    mensaje_malo_payload = json.dumps(
        {
            "evento_id": str(uuid4()),
            "tipo": "PolizaEmitida",
            "agregado_id": str(uuid4()),
            "ocurrido_en": "2026-11-06T12:00:00+00:00",
            "origen": "ms_polizas",
            "payload": {"usuario_id": str(usuario)},
        }
    ).encode("utf-8")

    async def _manejar_que_lanza(*args, **kwargs):
        raise RuntimeError("fallo inesperado procesando el evento")

    monkeypatch.setattr(kafka_consumer_module, "manejar_evento", _manejar_que_lanza)

    consumidor = ConsumidorMSK(_config(), uow, push)
    await consumidor.iniciar()
    consumidor._consumer._mensajes.append(_Mensaje(mensaje_malo_payload))

    await asyncio.wait_for(consumidor._consumer.ciclo_completo.wait(), timeout=1)

    assert not consumidor._tarea.done()
    await consumidor.detener()


async def test_detener_propaga_cancelacion_sin_lanzar(uow, consumer_falso):
    consumidor = ConsumidorMSK(_config(), uow, PushDoble())
    await consumidor.iniciar()

    await consumidor.detener()

    assert consumidor._consumer is None
    assert consumidor._tarea is None


async def test_detener_no_lanza_si_la_tarea_lanza_algo_distinto_a_cancelled(uow, consumer_falso):
    """Si awaitear la tarea cancelada lanza otra excepción (no
    CancelledError), detener() la atrapa y sigue -- nunca propaga."""
    consumidor = ConsumidorMSK(_config(), uow, PushDoble())
    await consumidor.iniciar()
    # Se reemplaza por una tarea que, al recibir la cancelación, lanza una
    # excepción distinta en vez de dejar propagar CancelledError -- simula
    # un bug real en el cuerpo de _bucle (p. ej. un finally que falla).
    anterior = consumidor._tarea
    anterior.cancel()
    try:
        await anterior
    except asyncio.CancelledError:
        pass

    async def _tarea_que_lanza_al_cancelar():
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            raise RuntimeError("fallo inesperado durante la cancelación") from None

    consumidor._tarea = asyncio.ensure_future(_tarea_que_lanza_al_cancelar())

    await consumidor.detener()  # no debe lanzar

    assert consumidor._tarea is None


async def test_detener_no_lanza_si_stop_falla(uow, consumer_falso):
    consumidor = ConsumidorMSK(_config(), uow, PushDoble())
    await consumidor.iniciar()
    consumidor._consumer.fallar_en_stop = True

    await consumidor.detener()  # no debe lanzar

    assert consumidor._consumer is None


def test_token_usa_el_firmador_iam(monkeypatch):
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

    assert provider.token() == "token-para-us-east-1"
