import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.api.v1 import rutas
from app.config import Settings
from app.domain.errores import ConsentimientoNoOtorgado, ErrorDominio, NoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.infrastructure.adaptadores import AdaptadorOpenDataStub, AdaptadorOpenFinanceStub
from app.infrastructure.cache import AdaptadorConCache, CacheRedis
from app.infrastructure.cache_fuentes import CacheEnMemoria
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo
from app.observabilidad import instrumentar

ESTADO_HTTP = {
    NoEncontrado: 404,
    TransicionInvalida: 409,
    ReglaDeNegocioViolada: 422,
    ConsentimientoNoOtorgado: 403,
}


def crear_app(config: Settings | None = None) -> FastAPI:
    config = config or Settings()
    logging.basicConfig(level=config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        motor = crear_motor(config)
        app.state.motor = motor
        app.state.fabrica_uow = fabrica_unidad_de_trabajo(motor)
        open_finance = AdaptadorOpenFinanceStub(config.doble_open_finance_latencia_ms, config.doble_open_finance_fallar)
        open_data = AdaptadorOpenDataStub(config.doble_open_data_latencia_ms, config.doble_open_data_fallar)
        redis = None
        if config.redis_cache_od_host:
            redis = Redis(host=config.redis_cache_od_host, port=config.redis_cache_od_port)
            cache = CacheRedis(redis)
            open_finance = AdaptadorConCache(
                open_finance, cache, "of", config.redis_cache_od_ttl_seconds, config.timeout_cache_ms
            )
            open_data = AdaptadorConCache(open_data, cache, "od", config.redis_cache_od_ttl_seconds, config.timeout_cache_ms)
        app.state.adaptador_open_finance = open_finance
        app.state.adaptador_open_data = open_data
        app.state.config = config
        app.state.cache_fuentes = CacheEnMemoria()
        yield
        if redis is not None:
            await redis.aclose()
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
