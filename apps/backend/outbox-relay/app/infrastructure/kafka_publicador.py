from __future__ import annotations

import json
import logging
import os
import ssl

from app.config import Settings
from app.domain.modelos import EventoOutbox

logger = logging.getLogger(__name__)


class MSKTokenProvider:
    """Proveedor de tokens OAUTHBEARER con IAM de AWS para MSK.

    Importa el firmador de forma perezosa: los tests no necesitan la dependencia
    instalada ni credenciales de AWS. Mismo patrón que
    apps/backend/notificaciones/app/infrastructure/kafka_consumer.py -- cada
    servicio es independiente, sin paquete compartido entre ellos en este repo.
    """

    def __init__(self, region: str) -> None:
        self._region = region

    def token(self) -> str:
        from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

        token, _ = MSKAuthTokenProvider.generate_auth_token(self._region)
        return token


class PublicadorMSK:
    """Publica eventos de outbox en `BusEventos` (MSK)."""

    def __init__(self, config: Settings) -> None:
        self._config = config
        self._producer = None

    @property
    def _region(self) -> str:
        return (
            self._config.aws_region
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1"
        )

    async def _asegurar_producer(self):
        if self._producer is None:
            from aiokafka import AIOKafkaProducer

            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._config.msk_bootstrap_brokers,
                security_protocol="SASL_SSL",
                # aiokafka >= 0.13 no crea el contexto TLS por su cuenta: con
                # SASL_SSL y ssl_context=None el constructor lanza "`ssl_context`
                # is mandatory if security_protocol=='SSL'" antes de conectar.
                ssl_context=ssl.create_default_context(),
                sasl_mechanism="OAUTHBEARER",
                sasl_oauth_token_provider=MSKTokenProvider(self._region),
            )
            await self._producer.start()
            logger.info("publicador_msk_iniciado", extra={"topico": self._config.msk_topic})
        return self._producer

    async def publicar(self, evento: EventoOutbox) -> None:
        producer = await self._asegurar_producer()
        await producer.send_and_wait(
            self._config.msk_topic,
            key=evento.clave().encode("utf-8"),
            value=json.dumps(evento.a_mensaje()).encode("utf-8"),
        )

    async def cerrar(self) -> None:
        """Detiene el producer. Idempotente y nunca lanza."""
        producer, self._producer = self._producer, None
        if producer is not None:
            try:
                await producer.stop()
            except Exception:
                logger.warning("publicador_msk_fallo_al_detener", exc_info=True)
