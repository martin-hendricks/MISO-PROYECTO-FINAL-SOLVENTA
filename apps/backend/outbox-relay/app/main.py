from __future__ import annotations

import asyncio
import logging
import signal

import uvicorn
from fastapi import FastAPI

from app.application.relay import bucle_relay
from app.config import Settings
from app.infrastructure.kafka_publicador import PublicadorMSK
from app.infrastructure.sql import RepositorioOutboxSQL, crear_motor
from app.observabilidad import instrumentar

logger = logging.getLogger(__name__)

# outbox-relay es un worker de polling en background, no una API: no expone
# routers de negocio. FastAPI se mantiene solo para reusar /health y /metrics
# ya instrumentados en observabilidad.py -- el chart de Helm
# (infra/k8s/charts/microservicio) exige httpGet para liveness/readiness, así
# que el pod necesita responder algo en el puerto configurado.
#
# (esquema, nombre del atributo de Settings con su DATABASE_URL) -- mapea
# cada esquema productor al campo de config correspondiente para resolver la
# URL real en main() antes de construir el FuenteOutbox/repositorio.
ESQUEMA_A_ATRIBUTO_CONFIG: tuple[tuple[str, str], ...] = (
    ("ms_cotizacion", "database_url_ms_cotizacion"),
    ("ms_suscripcion", "database_url_ms_suscripcion"),
    ("ms_pagos", "database_url_ms_pagos"),
    ("ms_perfilamiento", "database_url_ms_perfilamiento"),
    ("ms_polizas", "database_url_ms_polizas"),
    ("ms_siniestros", "database_url_ms_siniestros"),
    ("ms_identidad", "database_url_ms_identidad"),
)


def crear_app() -> FastAPI:
    app = FastAPI(title="outbox-relay", version="1.0.0")
    instrumentar(app)
    return app


app = crear_app()


async def main() -> None:
    config = Settings()
    logging.basicConfig(level=config.log_level)

    motores = []
    repositorios: list[RepositorioOutboxSQL] = []
    for esquema, atributo_config in ESQUEMA_A_ATRIBUTO_CONFIG:
        url = getattr(config, atributo_config)
        if not url:
            logger.warning("fuente_outbox_sin_configurar", extra={"esquema": esquema})
            continue
        motor = crear_motor(url)
        motores.append(motor)
        repositorios.append(RepositorioOutboxSQL(motor, esquema))

    publicador = PublicadorMSK(config)
    parar = asyncio.Event()

    servidor = uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=8080, log_level=config.log_level.lower())
    )

    def _parar(*_args: object) -> None:
        parar.set()
        servidor.should_exit = True

    loop = asyncio.get_running_loop()
    for señal in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(señal, _parar)

    try:
        await asyncio.gather(
            bucle_relay(repositorios, publicador, config.lote, config.intervalo_segundos, parar),
            servidor.serve(),
        )
    finally:
        await publicador.cerrar()
        for motor in motores:
            await motor.dispose()


if __name__ == "__main__":
    asyncio.run(main())
