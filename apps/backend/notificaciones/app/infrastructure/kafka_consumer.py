from __future__ import annotations

import asyncio
import logging
import os
import ssl

from app.application.manejadores import manejar_evento
from app.config import Settings
from app.domain.eventos import EventoBus
from app.domain.modelos import Notificacion
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.push import EnviadorPush

logger = logging.getLogger(__name__)


class MSKTokenProvider:
    """Proveedor de tokens OAUTHBEARER con IAM de AWS para MSK.

    Importa el firmador de forma perezosa: los tests no necesitan la dependencia
    instalada ni credenciales de AWS.
    """

    def __init__(self, region: str) -> None:
        self._region = region

    def token(self) -> str:
        from aws_msk_iam_sasl_signer import MSKAuthTokenProvider

        token, _ = MSKAuthTokenProvider.generate_auth_token(self._region)
        return token


class ConsumidorMSK:
    """Consumidor de `BusEventos` que convierte eventos de dominio en notificaciones."""

    def __init__(self, config: Settings, uow: FabricaUnidadDeTrabajo, push: EnviadorPush) -> None:
        self._config = config
        self._uow = uow
        self._push = push
        self._consumer = None
        self._tarea: asyncio.Task | None = None

    @property
    def _region(self) -> str:
        return (
            self._config.aws_region
            or os.environ.get("AWS_REGION")
            or os.environ.get("AWS_DEFAULT_REGION")
            or "us-east-1"
        )

    async def iniciar(self) -> None:
        """Arranca el consumidor y lanza el bucle de lectura en segundo plano."""
        if self._consumer is not None:
            return

        from aiokafka import AIOKafkaConsumer

        self._consumer = AIOKafkaConsumer(
            self._config.msk_topic,
            bootstrap_servers=self._config.msk_bootstrap_brokers,
            group_id=self._config.msk_consumer_group,
            security_protocol="SASL_SSL",
            # aiokafka >= 0.13 deja de construir el contexto TLS por su cuenta:
            # con SASL_SSL y ssl_context=None aborta en el constructor con
            # "`ssl_context` is mandatory if security_protocol=='SSL'", antes de
            # intentar conectar. El trust store del sistema basta porque MSK
            # presenta certificados de Amazon Trust Services.
            ssl_context=ssl.create_default_context(),
            sasl_mechanism="OAUTHBEARER",
            sasl_oauth_token_provider=MSKTokenProvider(self._region),
            auto_offset_reset="earliest",
            enable_auto_commit=True,
        )
        await self._consumer.start()
        self._tarea = asyncio.create_task(self._bucle(), name="consumidor-msk-notificaciones")
        logger.info(
            "consumidor_msk_iniciado",
            extra={"topico": self._config.msk_topic, "grupo": self._config.msk_consumer_group},
        )

    async def detener(self) -> None:
        """Detiene el bucle y el consumidor. Idempotente y nunca lanza."""
        tarea, self._tarea = self._tarea, None
        if tarea is not None:
            tarea.cancel()
            try:
                await tarea
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.warning("consumidor_msk_tarea_fallo_al_detener", exc_info=True)

        consumidor, self._consumer = self._consumer, None
        if consumidor is not None:
            try:
                await consumidor.stop()
            except Exception:
                logger.warning("consumidor_msk_fallo_al_detener", exc_info=True)

    async def _bucle(self) -> None:
        async for mensaje in self._consumer:
            try:
                evento = EventoBus.desde_mensaje(mensaje.value)
                if evento is None:
                    logger.warning(
                        "mensaje_msk_ignorado",
                        extra={"topico": mensaje.topic, "offset": mensaje.offset},
                    )
                    continue
                await manejar_evento(self._uow, self._push, evento)
            except Exception:
                logger.exception(
                    "error_procesando_mensaje_msk",
                    extra={
                        "topico": getattr(mensaje, "topic", None),
                        "offset": getattr(mensaje, "offset", None),
                    },
                )
                continue

    async def procesar_mensaje(self, valor: bytes | str | dict) -> Notificacion | None:
        """Procesa un mensaje sin Kafka; usado por los tests y por `_bucle`."""
        try:
            evento = EventoBus.desde_mensaje(valor)
        except ValueError:
            logger.warning("mensaje_msk_invalido", exc_info=True)
            return None
        if evento is None:
            logger.warning("mensaje_msk_ignorado")
            return None
        return await manejar_evento(self._uow, self._push, evento)
