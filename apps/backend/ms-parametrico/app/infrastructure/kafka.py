"""Productor de TopicoTelemetria con contrapresión explícita (EC-ESC-03).

- acks=all + idempotencia del productor: un 202 implica que el evento quedó replicado
  en las réplicas en sincronía, y los reintentos internos del productor no duplican.
- key = evento_id: todas las entregas de un evento van a la misma partición, así el
  consumidor las procesa en orden y la segunda se descarta por idempotencia.
- Semáforo de publicaciones en vuelo: cuando se llena, la réplica responde 429 en vez
  de acumular peticiones en memoria. El proveedor reintenta y el pico se reparte en el
  tiempo; el tópico (con su retención) es el almacén del rezago, no la RAM del pod.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import ssl

from aiokafka.abc import AbstractTokenProvider

from app.config import Settings
from app.domain.evento import EventoTelemetria
from app.ports.publicador import PublicadorNoDisponible, PublicadorSaturado

logger = logging.getLogger(__name__)


class MSKTokenProvider(AbstractTokenProvider):
    """Token OAUTHBEARER firmado con IAM. Mismo patrón que outbox-relay y
    notificaciones (cada servicio es independiente, sin paquete compartido)."""

    def __init__(self, region: str) -> None:
        self._region = region

    async def token(self) -> str:
        return await asyncio.get_running_loop().run_in_executor(None, self._token)

    def _token(self) -> str:
        from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

        token, _ = MSKAuthTokenProvider.generate_auth_token(self._region)
        return token


def opciones_conexion(config: Settings) -> dict:
    """PLAINTEXT para el Kafka local; SASL/IAM contra MSK."""
    if config.msk_auth_mechanism.upper() == "PLAINTEXT":
        return {"security_protocol": "PLAINTEXT"}
    region = config.aws_region or os.environ.get("AWS_REGION") or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    return {
        "security_protocol": "SASL_SSL",
        "ssl_context": ssl.create_default_context(),
        "sasl_mechanism": "OAUTHBEARER",
        "sasl_oauth_token_provider": MSKTokenProvider(region),
    }


class PublicadorKafka:
    def __init__(self, config: Settings, producer=None) -> None:
        self._config = config
        self._producer = producer
        self._iniciado = producer is not None
        self._en_vuelo = asyncio.Semaphore(config.max_publicaciones_en_vuelo)

    async def iniciar(self) -> None:
        if self._iniciado:
            return
        from aiokafka import AIOKafkaProducer

        self._producer = AIOKafkaProducer(
            bootstrap_servers=self._config.msk_bootstrap_brokers,
            acks="all",
            enable_idempotence=True,
            linger_ms=5,
            **opciones_conexion(self._config),
        )
        await self._producer.start()
        self._iniciado = True
        logger.info("publicador_telemetria_iniciado", extra={"topico": self._config.msk_topic})

    def listo(self) -> bool:
        return self._iniciado

    async def publicar(self, evento: EventoTelemetria) -> None:
        if self._en_vuelo.locked():
            raise PublicadorSaturado()
        async with self._en_vuelo:
            try:
                await asyncio.wait_for(
                    self._producer.send_and_wait(
                        self._config.msk_topic,
                        key=evento.evento_id.encode("utf-8"),
                        value=json.dumps(evento.a_mensaje()).encode("utf-8"),
                    ),
                    timeout=self._config.timeout_publicacion_segundos,
                )
            except Exception as exc:
                logger.warning("publicacion_telemetria_fallida", extra={"evento_id": evento.evento_id}, exc_info=True)
                raise PublicadorNoDisponible() from exc

    async def cerrar(self) -> None:
        producer, self._producer = self._producer, None
        self._iniciado = False
        if producer is not None:
            try:
                await producer.stop()
            except Exception:
                logger.warning("publicador_telemetria_fallo_al_detener", exc_info=True)
