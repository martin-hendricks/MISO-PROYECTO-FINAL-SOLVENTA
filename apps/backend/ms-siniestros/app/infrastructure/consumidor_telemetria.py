""":MotorParametrico — consumidor de TopicoTelemetria (decisión D5, opción B).

ms-parametrico (:ApiTelemetria) publica el evento canónico; este consumidor lo lleva al
mismo caso de uso que el POST /v1/eventos-parametricos, que ya es idempotente por
evento_id y atómico (una transacción para registrar y decidir, desembolso después).

Garantías (EC-ESC-04, "procesados exactamente una vez"):
- Commit manual del offset, y solo DESPUÉS de procesar. Si el pod cae a mitad, el
  mensaje se reentrega y la idempotencia por evento_id evita el segundo pago.
  Entrega al-menos-una-vez + consumidor idempotente = efecto exactamente una vez.
- Falla transitoria (BD, pasarela): no se avanza el offset; se reintenta con backoff.
  La partición se detiene a propósito: no se pierde ni se salta ningún evento.
- Mensaje que nunca se podrá procesar (JSON corrupto, contrato desconocido, regla de
  negocio violada): se registra y se avanza para no bloquear la partición. La DLQ
  productiva queda fuera de este alcance (README).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import ssl
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prometheus_client import Counter
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.application import casos_uso
from app.config import Settings
from app.domain.errores import ErrorDominio
from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import FabricaUnidadDeTrabajo

logger = logging.getLogger(__name__)

MENSAJES = Counter(
    "solventa_siniestros_telemetria_mensajes_total",
    "Mensajes de TopicoTelemetria por resultado del procesamiento",
    ["resultado"],  # procesado | duplicado | descartado | reintento
)

VERSION_CONTRATO = 1


class MensajeDescartable(Exception):
    """El mensaje no se podrá procesar nunca: reintentarlo bloquearía la partición."""


class _Cobertura(BaseModel):
    umbral: Decimal
    monto: Decimal
    vigente: bool = True
    poliza_id: UUID | None = None
    poliza_numero: str | None = Field(default=None, max_length=60)
    usuario_id: UUID | None = None


class EventoTelemetriaEntrante(BaseModel):
    """Copia local del contrato canónico de ms-parametrico (app/domain/evento.py).
    Cada servicio valida lo que recibe; no hay paquete compartido en este repo."""

    model_config = ConfigDict(extra="ignore")

    version: int
    evento_id: str = Field(min_length=1, max_length=120)
    proveedor: str
    tipo: str
    valor: Decimal
    ocurrido_en: datetime
    ramo: str | None = Field(default=None, max_length=60)
    descripcion: str | None = Field(default=None, max_length=200)
    cobertura: _Cobertura


def leer_mensaje(valor: bytes | str) -> EventoTelemetriaEntrante:
    try:
        evento = EventoTelemetriaEntrante.model_validate(json.loads(valor))
    except (ValueError, ValidationError) as exc:
        raise MensajeDescartable(f"mensaje ilegible: {exc}") from exc
    if evento.version != VERSION_CONTRATO:
        raise MensajeDescartable(f"versión de contrato no soportada: {evento.version}")
    return evento


async def procesar_mensaje(
    uow: FabricaUnidadDeTrabajo, adaptador: AdaptadorDesembolso, valor: bytes | str
) -> casos_uso.ResultadoIngesta:
    """Procesa un mensaje sin Kafka (lo usan el bucle y las pruebas). Lanza
    MensajeDescartable si reintentar no tiene sentido; cualquier otra excepción es
    transitoria y el llamador debe reintentar sin avanzar el offset."""
    evento = leer_mensaje(valor)
    c = evento.cobertura
    try:
        return await casos_uso.recibir_evento_parametrico(
            uow,
            adaptador,
            evento.evento_id,
            evento.valor,
            c.umbral,
            c.vigente,
            c.monto,
            poliza_id=c.poliza_id,
            usuario_id=c.usuario_id,
            ramo=evento.ramo,
            poliza_numero=c.poliza_numero,
            descripcion=evento.descripcion,
            origen=casos_uso.ORIGEN_TOPICO_TELEMETRIA,
        )
    except ErrorDominio as exc:
        # Reglas deterministas (monto no positivo, evento sin id, transición inválida):
        # la misma entrada fallará igual en cada reintento.
        raise MensajeDescartable(f"{exc.codigo}: {exc.mensaje}") from exc


def opciones_conexion(config: Settings) -> dict:
    if config.msk_auth_mechanism.upper() == "PLAINTEXT":
        return {"security_protocol": "PLAINTEXT"}
    from app.infrastructure.msk import MSKTokenProvider

    region = config.aws_region or os.environ.get("AWS_DEFAULT_REGION") or "us-east-1"
    return {
        "security_protocol": "SASL_SSL",
        "ssl_context": ssl.create_default_context(),
        "sasl_mechanism": "OAUTHBEARER",
        "sasl_oauth_token_provider": MSKTokenProvider(region),
    }


class ConsumidorTelemetria:
    def __init__(
        self,
        config: Settings,
        uow: FabricaUnidadDeTrabajo,
        adaptador: AdaptadorDesembolso,
        consumer=None,
    ) -> None:
        self._config = config
        self._uow = uow
        self._adaptador = adaptador
        self._consumer = consumer
        self._tarea: asyncio.Task | None = None

    async def iniciar(self) -> None:
        """No bloquea el arranque del servicio: la conexión se reintenta en segundo plano.
        Si MSK no está disponible, solo se detiene el canal paramétrico; el aviso
        asistido y las consultas de ms-siniestros siguen sirviendo."""
        if self._consumer is None:
            from aiokafka import AIOKafkaConsumer

            self._consumer = AIOKafkaConsumer(
                self._config.msk_topic_telemetria,
                bootstrap_servers=self._config.msk_bootstrap_brokers,
                group_id=self._config.msk_consumer_group_telemetria,
                enable_auto_commit=False,
                auto_offset_reset="earliest",
                **opciones_conexion(self._config),
            )
        self._tarea = asyncio.create_task(self._conectar_y_consumir(), name="consumidor-telemetria")

    async def _conectar_y_consumir(self) -> None:
        espera = self._config.consumidor_backoff_inicial_segundos
        while True:
            try:
                await self._consumer.start()
                break
            except Exception:
                logger.warning("consumidor_telemetria_sin_conexion", extra={"espera_s": espera}, exc_info=True)
                await asyncio.sleep(espera)
                espera = min(espera * 2, self._config.consumidor_backoff_maximo_segundos)
        logger.info(
            "consumidor_telemetria_iniciado",
            extra={"topico": self._config.msk_topic_telemetria, "grupo": self._config.msk_consumer_group_telemetria},
        )
        await self.bucle()

    async def detener(self) -> None:
        tarea, self._tarea = self._tarea, None
        if tarea is not None:
            tarea.cancel()
            try:
                await tarea
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.warning("consumidor_telemetria_tarea_fallo_al_detener", exc_info=True)
        consumidor, self._consumer = self._consumer, None
        if consumidor is not None:
            try:
                await consumidor.stop()
            except Exception:
                logger.warning("consumidor_telemetria_fallo_al_detener", exc_info=True)

    async def bucle(self) -> None:
        while True:
            lote = await self._consumer.getmany(timeout_ms=1000, max_records=self._config.consumidor_lote_maximo)
            for particion, mensajes in lote.items():
                for mensaje in mensajes:
                    await self._procesar_hasta_lograrlo(mensaje)
                    try:
                        await self._consumer.commit({particion: mensaje.offset + 1})
                    except Exception:
                        # Rebalanceo: la partición pasó a otra réplica, que reentregará
                        # desde el último offset confirmado. La idempotencia lo absorbe.
                        logger.warning("commit_offset_fallido", extra={"offset": mensaje.offset}, exc_info=True)

    async def _procesar_hasta_lograrlo(self, mensaje) -> None:
        espera = self._config.consumidor_backoff_inicial_segundos
        while True:
            try:
                resultado = await procesar_mensaje(self._uow, self._adaptador, mensaje.value)
            except MensajeDescartable as exc:
                MENSAJES.labels("descartado").inc()
                logger.error(
                    "mensaje_telemetria_descartado",
                    extra={"particion": mensaje.partition, "offset": mensaje.offset, "motivo": str(exc)},
                )
                return
            except Exception:
                MENSAJES.labels("reintento").inc()
                logger.warning(
                    "mensaje_telemetria_reintento",
                    extra={"particion": mensaje.partition, "offset": mensaje.offset, "espera_s": espera},
                    exc_info=True,
                )
                await asyncio.sleep(espera)
                espera = min(espera * 2, self._config.consumidor_backoff_maximo_segundos)
                continue
            MENSAJES.labels("procesado" if resultado.procesado else "duplicado").inc()
            return
