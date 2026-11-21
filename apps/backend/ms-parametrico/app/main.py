import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import rutas
from app.config import Settings
from app.infrastructure.kafka import PublicadorKafka
from app.infrastructure.memoria import PublicadorEnMemoria
from app.observabilidad import instrumentar

log = logging.getLogger(__name__)


def crear_app(config: Settings | None = None, publicador=None) -> FastAPI:
    config = config or Settings()
    logging.basicConfig(level=config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        kafka = None
        if app.state.publicador is None:
            if config.msk_bootstrap_brokers:
                kafka = PublicadorKafka(config)
                await kafka.iniciar()
                app.state.publicador = kafka
            else:
                log.warning("MSK_BOOTSTRAP_BROKERS vacío: los eventos quedan en memoria (solo desarrollo)")
                app.state.publicador = PublicadorEnMemoria()
        yield
        if kafka is not None:
            await kafka.cerrar()

    app = FastAPI(title=config.service_name, version="0.1.0", lifespan=lifespan)
    app.state.config = config
    app.state.publicador = publicador
    instrumentar(app)
    app.include_router(rutas.router)
    return app


app = crear_app()
