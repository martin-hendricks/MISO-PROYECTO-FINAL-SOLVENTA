import json

import pytest

from app.config import Settings
from app.infrastructure.kafka_publicador import MSKTokenProvider, PublicadorMSK

from .dobles import evento_outbox


def _config(**cambios) -> Settings:
    datos = {
        "msk_bootstrap_brokers": "b-1.solventa.kafka.us-east-1.amazonaws.com:9098",
        "msk_topic": "BusEventos",
    }
    datos.update(cambios)
    return Settings(**datos)


async def test_cerrar_sin_iniciar_no_lanza():
    publicador = PublicadorMSK(_config())

    await publicador.cerrar()
    await publicador.cerrar()


def test_cerrar_sin_iniciar_deja_el_estado_seguro():
    publicador = PublicadorMSK(_config())
    assert publicador._producer is None


def test_provider_de_tokens_usa_la_region_configurada():
    provider = MSKTokenProvider("us-east-1")
    assert provider._region == "us-east-1"


def test_region_usa_la_configurada_explicitamente():
    publicador = PublicadorMSK(_config(aws_region="eu-west-1"))
    assert publicador._region == "eu-west-1"


def test_region_cae_a_variable_de_entorno(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    publicador = PublicadorMSK(_config(aws_region=""))
    assert publicador._region == "us-west-2"


def test_region_por_defecto_cae_a_us_east_1(monkeypatch):
    monkeypatch.delenv("AWS_REGION", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    publicador = PublicadorMSK(_config(aws_region=""))
    assert publicador._region == "us-east-1"


class _ProducerFalso:
    """Doble de AIOKafkaProducer: start/stop/send_and_wait sin red real."""

    instancias: list["_ProducerFalso"] = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.started = False
        self.stopped = False
        self.enviados: list[tuple[str, bytes, bytes]] = []
        _ProducerFalso.instancias.append(self)

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True

    async def send_and_wait(self, topic, key, value):
        self.enviados.append((topic, key, value))


@pytest.fixture(autouse=True)
def _limpiar_instancias_producer():
    _ProducerFalso.instancias.clear()
    yield
    _ProducerFalso.instancias.clear()


@pytest.fixture
def producer_falso(monkeypatch):
    import aiokafka

    monkeypatch.setattr(aiokafka, "AIOKafkaProducer", _ProducerFalso)
    return _ProducerFalso


async def test_publicar_arranca_el_producer_una_sola_vez(producer_falso):
    publicador = PublicadorMSK(_config())
    evento = evento_outbox()

    await publicador.publicar(evento)
    await publicador.publicar(evento_outbox())

    assert len(producer_falso.instancias) == 1
    assert producer_falso.instancias[0].started is True
    assert len(producer_falso.instancias[0].enviados) == 2


async def test_publicar_envia_la_clave_y_el_mensaje_correctos(producer_falso):
    publicador = PublicadorMSK(_config())
    evento = evento_outbox()

    await publicador.publicar(evento)

    topic, key, value = producer_falso.instancias[0].enviados[0]
    assert topic == "BusEventos"
    assert key == evento.clave().encode("utf-8")
    assert json.loads(value) == evento.a_mensaje()


async def test_cerrar_detiene_el_producer_real(producer_falso):
    publicador = PublicadorMSK(_config())
    await publicador.publicar(evento_outbox())

    await publicador.cerrar()

    assert producer_falso.instancias[0].stopped is True
    assert publicador._producer is None


async def test_cerrar_no_lanza_si_stop_falla(producer_falso):
    publicador = PublicadorMSK(_config())
    await publicador.publicar(evento_outbox())
    producer_falso.instancias[0].stop = _stop_que_falla

    await publicador.cerrar()  # no debe lanzar

    assert publicador._producer is None


async def _stop_que_falla():
    raise RuntimeError("fallo simulado al detener el producer")


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
