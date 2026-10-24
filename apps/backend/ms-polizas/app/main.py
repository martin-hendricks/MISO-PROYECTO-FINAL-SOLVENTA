import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import rutas
from app.config import Settings
from app.domain.errores import (
    DependenciaNoDisponible,
    ErrorDominio,
    NoEncontrado,
    ReglaDeNegocioViolada,
    TransicionInvalida,
)
from app.infrastructure.precondiciones import CobrosHTTP, SuscripcionesHTTP
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo
from app.observabilidad import instrumentar

ESTADO_HTTP = {
    NoEncontrado: 404,
    ReglaDeNegocioViolada: 422,
    TransicionInvalida: 409,
    DependenciaNoDisponible: 503,
}


def crear_app(config: Settings | None = None) -> FastAPI:
    config = config or Settings()
    logging.basicConfig(level=config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        motor = crear_motor(config)
        http_suscripcion = httpx.AsyncClient(base_url=config.ms_suscripcion_url, timeout=config.timeout_dependencias)
        http_pagos = httpx.AsyncClient(base_url=config.ms_pagos_url, timeout=config.timeout_dependencias)
        app.state.fabrica_uow = fabrica_unidad_de_trabajo(motor)
        app.state.suscripciones = SuscripcionesHTTP(http_suscripcion)
        app.state.cobros = CobrosHTTP(http_pagos)
        yield
        await http_suscripcion.aclose()
        await http_pagos.aclose()
        await motor.dispose()

    app = FastAPI(title=config.service_name, version="1.0.0", lifespan=lifespan)
    instrumentar(app)
    app.include_router(rutas.router)

    @app.exception_handler(ErrorDominio)
    async def error_dominio(_: Request, exc: ErrorDominio):
        return JSONResponse(
            status_code=ESTADO_HTTP.get(type(exc), 400),
            content={"codigo": exc.codigo, "mensaje": exc.mensaje},
        )

    return app


app = crear_app()
