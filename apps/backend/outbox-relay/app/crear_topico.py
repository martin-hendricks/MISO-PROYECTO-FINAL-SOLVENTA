"""Crea los tópicos de Kafka que MSK no provisiona por sí solo.

El clúster corre con `auto.create.topics.enable=false` (ver
infra/terraform/modules/msk/variables.tf), así que `BusEventos` debe existir
antes del primer publish: si no, `send_and_wait` falla con
UNKNOWN_TOPIC_OR_PARTITION y el relay reintenta el lote para siempre.

Se ejecuta una sola vez desde un pod con la ServiceAccount `outbox-relay`, que
es la única con `kafka-cluster:CreateTopic` (modules/irsa_aplicacion). El
deploy lo lanza automáticamente con el Job
`infra/k8s/platform/crear-topico-buseventos.yaml`; este módulo también sirve
para correrlo a mano:

    kubectl -n solventa run crear-topico --rm -it --restart=Never \
      --image=<ECR>/solventa-minimo-outbox-relay:<tag> \
      --overrides='{"spec":{"serviceAccountName":"outbox-relay"}}' \
      -- python -m app.crear_topico --brokers "$MSK_BOOTSTRAP_BROKERS" BusEventos

Es idempotente: si el tópico ya existe termina con código 0, para que se pueda
volver a correr sin efectos.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
from collections.abc import Sequence

logger = logging.getLogger(__name__)

PARTICIONES_POR_DEFECTO = 6  # = num_partitions del módulo msk
REPLICAS_POR_DEFECTO = 2  # = default_replication_factor (2 brokers)


def faltantes(existentes: Sequence[str], solicitados: Sequence[str]) -> list[str]:
    """Tópicos a crear, sin duplicados y conservando el orden pedido."""
    ya = set(existentes)
    vistos: set[str] = set()
    pendientes: list[str] = []
    for nombre in solicitados:
        if nombre in ya or nombre in vistos:
            continue
        vistos.add(nombre)
        pendientes.append(nombre)
    return pendientes


def _region(explicita: str | None) -> str:
    return (
        explicita
        or os.environ.get("AWS_REGION")
        or os.environ.get("AWS_DEFAULT_REGION")
        or "us-east-1"
    )


async def crear(
    brokers: str,
    topicos: Sequence[str],
    particiones: int,
    replicas: int,
    region: str,
) -> list[str]:
    """Crea los tópicos que falten y devuelve sus nombres."""
    # Imports perezosos: el resto del módulo (y sus tests) no necesita aiokafka.
    from aiokafka.admin import AIOKafkaAdminClient, NewTopic
    from aiokafka.errors import TopicAlreadyExistsError

    from app.infrastructure.kafka_publicador import MSKTokenProvider

    admin = AIOKafkaAdminClient(
        bootstrap_servers=brokers,
        security_protocol="SASL_SSL",
        sasl_mechanism="OAUTHBEARER",
        sasl_oauth_token_provider=MSKTokenProvider(region),
    )
    await admin.start()
    creados: list[str] = []
    try:
        for nombre in topicos:
            try:
                await admin.create_topics(
                    [
                        NewTopic(
                            name=nombre,
                            num_partitions=particiones,
                            replication_factor=replicas,
                        )
                    ]
                )
            except TopicAlreadyExistsError:
                logger.info("topico_ya_existe", extra={"topico": nombre})
                continue
            creados.append(nombre)
            logger.info("topico_creado", extra={"topico": nombre})
    finally:
        await admin.close()
    return creados


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Crea tópicos en MSK de forma idempotente."
    )
    parser.add_argument(
        "topicos",
        nargs="+",
        help="Nombres de tópico a crear (p. ej. BusEventos).",
    )
    parser.add_argument(
        "--brokers",
        default=os.environ.get("MSK_BOOTSTRAP_BROKERS", ""),
        help="Bootstrap brokers SASL/IAM (por defecto MSK_BOOTSTRAP_BROKERS).",
    )
    parser.add_argument(
        "--particiones",
        type=int,
        default=PARTICIONES_POR_DEFECTO,
        help=f"Particiones del tópico (por defecto {PARTICIONES_POR_DEFECTO}).",
    )
    parser.add_argument(
        "--replicas",
        type=int,
        default=REPLICAS_POR_DEFECTO,
        help=f"Factor de replicación (por defecto {REPLICAS_POR_DEFECTO}).",
    )
    parser.add_argument(
        "--region",
        default=None,
        help="Región de AWS para firmar el token (por defecto AWS_REGION).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
    args = _parser().parse_args(argv)

    if not args.brokers:
        logger.error("faltan_brokers: pasa --brokers o define MSK_BOOTSTRAP_BROKERS")
        return 2

    creados = asyncio.run(
        crear(
            brokers=args.brokers,
            topicos=args.topicos,
            particiones=args.particiones,
            replicas=args.replicas,
            region=_region(args.region),
        )
    )
    if creados:
        print(f"topicos_creados={','.join(creados)}")
    else:
        print(f"topicos_sin_cambios={','.join(args.topicos)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
