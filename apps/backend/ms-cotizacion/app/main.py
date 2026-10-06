import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1 import rutas
from app.api.v1.schemas import ErrorSalida
from app.config import Settings
from app.dependencies import componer
from app.domain.errores import ErrorDominio, NoEncontrado, ReglaDeNegocioViolada
from app.observabilidad import instrumentar

ESTADO_HTTP = {NoEncontrado: 404}


def _estado_http(exc: ErrorDominio) -> int:
    if isinstance(exc, ReglaDeNegocioViolada):
        return 422
    return ESTADO_HTTP.get(type(exc), 400)


def crear_app(config: Settings | None = None) -> FastAPI:
    config = config or Settings()
    logging.basicConfig(level=config.log_level)

    app = FastAPI(title=config.service_name, version="1.0.0")
    app.state.colaboradores = componer(config)
    instrumentar(app)
    app.include_router(rutas.router)

    @app.exception_handler(RequestValidationError)
    async def solicitud_invalida(_: Request, exc: RequestValidationError):
        error = exc.errors()[0]
        campo = ".".join(str(p) for p in error["loc"] if p != "body") or None
        cuerpo = ErrorSalida(codigo="solicitud_invalida", mensaje=error["msg"], campo=campo)
        return JSONResponse(status_code=422, content=cuerpo.model_dump(by_alias=True, exclude_none=True))

    @app.exception_handler(ErrorDominio)
    async def error_dominio(_: Request, exc: ErrorDominio):
        cuerpo = ErrorSalida(
            codigo=exc.codigo, mensaje=exc.mensaje, campo=exc.campo, rango_valido=exc.rango_valido
        )
        return JSONResponse(
            status_code=_estado_http(exc),
            content=cuerpo.model_dump(by_alias=True, exclude_none=True),
        )

    return app


app = crear_app()
