import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import rutas
from app.clients.base import RechazoDelNucleo, RecursoNoEncontrado, ServicioNoDisponible
from app.config import Settings
from app.observabilidad import instrumentar

logger = logging.getLogger(__name__)


def crear_app(config: Settings | None = None) -> FastAPI:
    config = config or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        async with httpx.AsyncClient(base_url=config.ms_ejemplo_url, timeout=config.timeout_nucleo_s) as http:
            app.state.http_ms_ejemplo = http
            yield

    app = FastAPI(title=config.service_name, version="1.0.0", lifespan=lifespan)
    app.state.config = config
    instrumentar(app)
    app.include_router(rutas.router)

    @app.exception_handler(ServicioNoDisponible)
    async def no_disponible(_: Request, exc: ServicioNoDisponible):
        logger.warning("servicio no disponible: %s", exc.servicio)
        return JSONResponse(
            status_code=503,
            content={"codigo": "servicio_no_disponible", "mensaje": "Intenta de nuevo en unos minutos"},
        )

    @app.exception_handler(RecursoNoEncontrado)
    async def no_encontrado(_: Request, __: RecursoNoEncontrado):
        return JSONResponse(status_code=404, content={"codigo": "no_encontrado", "mensaje": "No existe"})

    @app.exception_handler(RechazoDelNucleo)
    async def rechazo(_: Request, exc: RechazoDelNucleo):
        return JSONResponse(status_code=exc.status, content={"codigo": exc.codigo, "mensaje": exc.mensaje})

    return app


app = crear_app()
