import asyncio
import json
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.domain.evento import Cobertura, EventoInvalido, EventoTelemetria
from app.infrastructure.kafka import PublicadorKafka, opciones_conexion
from app.ports.publicador import PublicadorNoDisponible, PublicadorSaturado

from .conftest import config_prueba


def _evento(evento_id="vuelos:R-1") -> EventoTelemetria:
    return EventoTelemetria(
        evento_id=evento_id,
        proveedor="vuelos",
        tipo="retraso_vuelo",
        valor=Decimal("190"),
        ocurrido_en=datetime(2026, 11, 20, 14, tzinfo=UTC),
        ramo="clima-vuelos",
        descripcion="Retraso",
        cobertura=Cobertura(umbral=Decimal("120"), monto=Decimal("180000.00")),
    )


class ProductorFalso:
    """Con bloquear=True el envío espera a que la prueba lo libere: así se simula un
    broker lento sin depender de tiempos (el CI prohíbe esperas reales en las pruebas)."""

    def __init__(self, bloquear=False, error=None):
        self.enviados = []
        self._error = error
        self.entro = asyncio.Event()
        self.liberar = asyncio.Event()
        if not bloquear:
            self.liberar.set()

    async def send_and_wait(self, topico, key, value):
        self.entro.set()
        await self.liberar.wait()
        if self._error:
            raise self._error
        self.enviados.append((topico, key, value))


async def test_publica_en_el_topico_con_key_igual_al_evento_id():
    productor = ProductorFalso()
    publicador = PublicadorKafka(config_prueba(), producer=productor)

    await publicador.publicar(_evento())

    [(topico, key, valor)] = productor.enviados
    assert topico == "TopicoTelemetria"
    assert key == b"vuelos:R-1"
    mensaje = json.loads(valor)
    assert mensaje["version"] == 1
    assert mensaje["evento_id"] == "vuelos:R-1"
    assert mensaje["valor"] == "190"
    assert mensaje["cobertura"] == {
        "umbral": "120",
        "monto": "180000.00",
        "vigente": True,
        "poliza_id": None,
        "poliza_numero": None,
        "usuario_id": None,
    }


async def test_con_el_cupo_lleno_rechaza_en_vez_de_encolar():
    productor = ProductorFalso(bloquear=True)
    publicador = PublicadorKafka(config_prueba(max_publicaciones_en_vuelo=1), producer=productor)

    en_vuelo = asyncio.create_task(publicador.publicar(_evento("vuelos:A")))
    await productor.entro.wait()  # A ocupa el único cupo
    with pytest.raises(PublicadorSaturado):
        await publicador.publicar(_evento("vuelos:B"))
    productor.liberar.set()
    await en_vuelo

    assert [k for _, k, _ in productor.enviados] == [b"vuelos:A"]


async def test_libera_el_cupo_al_terminar():
    productor = ProductorFalso()
    publicador = PublicadorKafka(config_prueba(max_publicaciones_en_vuelo=1), producer=productor)

    await publicador.publicar(_evento("vuelos:A"))
    await publicador.publicar(_evento("vuelos:B"))

    assert len(productor.enviados) == 2


async def test_si_el_broker_no_confirma_a_tiempo_el_evento_no_se_acepta():
    publicador = PublicadorKafka(
        config_prueba(timeout_publicacion_segundos=0.05), producer=ProductorFalso(bloquear=True)
    )  # el broker nunca confirma

    with pytest.raises(PublicadorNoDisponible):
        await publicador.publicar(_evento())


async def test_error_del_broker_se_traduce_a_no_disponible():
    publicador = PublicadorKafka(config_prueba(), producer=ProductorFalso(error=RuntimeError("broker caído")))

    with pytest.raises(PublicadorNoDisponible):
        await publicador.publicar(_evento())


def test_plaintext_para_local_e_iam_para_msk():
    assert opciones_conexion(config_prueba(msk_auth_mechanism="PLAINTEXT")) == {"security_protocol": "PLAINTEXT"}
    msk = opciones_conexion(config_prueba(msk_auth_mechanism="AWS_MSK_IAM"))
    assert msk["security_protocol"] == "SASL_SSL"
    assert msk["sasl_mechanism"] == "OAUTHBEARER"


def test_evento_canonico_exige_id_y_monto_positivo():
    with pytest.raises(EventoInvalido):
        _evento(evento_id="  ")
    with pytest.raises(EventoInvalido):
        EventoTelemetria(
            evento_id="x",
            proveedor="vuelos",
            tipo="retraso_vuelo",
            valor=Decimal("1"),
            ocurrido_en=datetime.now(UTC),
            ramo="clima-vuelos",
            descripcion="",
            cobertura=Cobertura(umbral=Decimal("1"), monto=Decimal("0")),
        )
