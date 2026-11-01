import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import rutas, rutas_cotizaciones
from app.config import Settings
from app.domain.errores import (
    DependenciaNoDisponible,
    ErrorDominio,
    NoEncontrado,
    ReglaDeNegocioViolada,
    TransicionInvalida,
)
from app.infrastructure.adaptador_perfil_perfilamiento import (
    AdaptadorPerfilRiesgoPerfilamiento,
    AdaptadorPerfilRiesgoPorProducto,
)
from app.infrastructure.adaptador_perfil_stub import AdaptadorPerfilRiesgoStub
from app.infrastructure.catalogo_sql import CatalogoSQL
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo
from app.infrastructure.suscripciones import SuscripcionesHTTP
from app.observabilidad import instrumentar

ESTADO_HTTP = {
    NoEncontrado: 404,
    TransicionInvalida: 409,
    ReglaDeNegocioViolada: 422,
    DependenciaNoDisponible: 503,
}


def estado_http(exc: ErrorDominio) -> int:
    return next((estado for tipo, estado in ESTADO_HTTP.items() if isinstance(exc, tipo)), 400)


def crear_app(config: Settings | None = None) -> FastAPI:
    config = config or Settings()
    logging.basicConfig(level=config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        motor = crear_motor(config)
        http = httpx.AsyncClient(base_url=config.ms_suscripcion_url, timeout=config.timeout_dependencias)
        http_perfilamiento = httpx.AsyncClient(
            base_url=config.ms_perfilamiento_url, timeout=config.timeout_dependencias
        )
        perfilamiento = AdaptadorPerfilRiesgoPerfilamiento(http_perfilamiento)
        app.state.fabrica_uow = fabrica_unidad_de_trabajo(motor)
        app.state.catalogo = await CatalogoSQL.cargar(motor)
        app.state.adaptador_perfil_riesgo = AdaptadorPerfilRiesgoPorProducto(
            {producto: perfilamiento for producto in config.productos_perfil_perfilamiento},
            por_defecto=AdaptadorPerfilRiesgoStub(),
        )
        app.state.suscripciones = SuscripcionesHTTP(http)
        app.state.config = config
        yield
        await http_perfilamiento.aclose()
        await http.aclose()
        await motor.dispose()

    app = FastAPI(title=config.service_name, version="1.0.0", lifespan=lifespan)
    instrumentar(app)
    app.include_router(rutas.router)
    app.include_router(rutas_cotizaciones.router)

    @app.exception_handler(ErrorDominio)
    async def error_dominio(_: Request, exc: ErrorDominio):
        return JSONResponse(
            status_code=estado_http(exc),
            content={"codigo": exc.codigo, "mensaje": exc.mensaje},
        )

    return app


app = crear_app()
