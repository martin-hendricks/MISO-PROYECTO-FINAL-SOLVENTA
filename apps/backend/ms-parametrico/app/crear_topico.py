"""Crea TopicoTelemetria, que MSK no provisiona por sí solo.

El clúster corre con auto.create.topics.enable=false, así que el tópico debe existir
antes del primer publish. Se ejecuta una sola vez desde un pod con la ServiceAccount
`ms-parametrico`, dueña del tópico y única con kafka-cluster:CreateTopic sobre él
(modules/irsa_aplicacion). El deploy lo lanza con el Job
infra/k8s/platform/crear-topico-telemetria.yaml; en local lo hace el servicio
`crear-topico-telemetria` de apps/backend/docker-compose.yml.

12 particiones: acotan cuántas réplicas de ms-siniestros consumen en paralelo y
superan su maxReplicas (6). Mismo patrón que outbox-relay/app/crear_topico.py.
Idempotente: si el tópico ya existe termina con código 0.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from app.config import Settings
from app.infrastructure.kafka import opciones_conexion

logger = logging.getLogger(__name__)

TOPICO = "TopicoTelemetria"
PARTICIONES_POR_DEFECTO = 12
REPLICAS_POR_DEFECTO = 2  # = default_replication_factor (2 brokers)


async def crear(config: Settings, particiones: int, replicas: int) -> bool:
    """Crea el tópico si falta. Devuelve True si lo creó."""
    from aiokafka.admin import AIOKafkaAdminClient, NewTopic
    from aiokafka.errors import TopicAlreadyExistsError

    admin = AIOKafkaAdminClient(bootstrap_servers=config.msk_bootstrap_brokers, **opciones_conexion(config))
    await admin.start()
    try:
        await admin.create_topics(
            [NewTopic(name=config.msk_topic, num_partitions=particiones, replication_factor=replicas)]
        )
    except TopicAlreadyExistsError:
        logger.info("topico_ya_existe", extra={"topico": config.msk_topic})
        return False
    finally:
        await admin.close()
    logger.info("topico_creado", extra={"topico": config.msk_topic, "particiones": particiones})
    return True


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    parser = argparse.ArgumentParser(description=f"Crea {TOPICO} de forma idempotente.")
    parser.add_argument("--particiones", type=int, default=PARTICIONES_POR_DEFECTO)
    parser.add_argument("--replicas", type=int, default=REPLICAS_POR_DEFECTO)
    args = parser.parse_args(argv)

    config = Settings()
    if not config.msk_bootstrap_brokers:
        logger.error("faltan_brokers: define MSK_BOOTSTRAP_BROKERS")
        return 2

    creado = asyncio.run(crear(config, args.particiones, args.replicas))
    print(f"topico_{'creado' if creado else 'sin_cambios'}={config.msk_topic}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
