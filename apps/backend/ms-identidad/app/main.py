import logging
import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import rutas, rutas_clientes
from app.config import Settings
from app.domain.errores import (
    Conflicto,
    CredencialesInvalidas,
    CuentaDuplicada,
    CuentaInactiva,
    DependenciaNoDisponible,
    ErrorDominio,
    IdentidadNoVerificada,
    NoEncontrado,
    ReglaDeNegocioViolada,
)
from app.infrastructure.consentimiento_http import ClienteConsentimientoHTTP
from app.infrastructure.kyc import VerificadorKYCStub
from app.infrastructure.perfilamiento_http import ClientePerfilamientoHTTP
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo
from app.infrastructure.token_servicio import token_de_servicio
from app.observabilidad import instrumentar

ESTADO_HTTP = {
    CuentaDuplicada: 409,
    Conflicto: 409,
    CredencialesInvalidas: 401,
    CuentaInactiva: 403,
    NoEncontrado: 404,
    IdentidadNoVerificada: 422,
    ReglaDeNegocioViolada: 422,
    DependenciaNoDisponible: 503,
}


def crear_app(config: Settings | None = None) -> FastAPI:
    config = config or Settings()
    logging.basicConfig(level=config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        motor = crear_motor(config)
        app.state.motor = motor
        app.state.fabrica_uow = fabrica_unidad_de_trabajo(motor)
        app.state.verificador_kyc = VerificadorKYCStub(
            config.doble_kyc_latencia_ms, config.doble_kyc_fallar, config.documentos_rechazados_kyc()
        )
        # Clientes HTTP hacia ms-consentimiento (habeas data) y ms-perfilamiento
        # (perfilamiento hipotecario), usados solo para resolver el campo
        # "consentimiento" del listado de clientes (HU-141). Ambos adaptadores
        # degradan a False si el servicio no responde -- ver
        # infrastructure/consentimiento_http.py y perfilamiento_http.py.
        #
        # ms-consentimiento ya exige autenticacion en sus endpoints (no acepta
        # llamadas sin token). El token de servicio (rol "servicio") dura solo
        # 5 minutos (ver token_servicio.py) -- no puede fijarse una vez como
        # header del AsyncClient (viviria mas que eso en un proceso de larga
        # duracion); ClienteConsentimientoHTTP lo genera de nuevo en cada
        # llamada, por eso recibe el secreto, no un token ya armado.
        secreto = os.environ.get("SOLVENTA_TOKEN_SECRET", "")
        async with (
            httpx.AsyncClient(
                base_url=config.ms_consentimiento_url, timeout=config.timeout_consentimiento_s
            ) as http_consentimiento,
            httpx.AsyncClient(
                base_url=config.ms_perfilamiento_url, timeout=config.timeout_consentimiento_s
            ) as http_perfilamiento,
        ):
            app.state.cliente_consentimiento = ClienteConsentimientoHTTP(http_consentimiento, secreto)
            app.state.cliente_perfilamiento = ClientePerfilamientoHTTP(http_perfilamiento)
            yield
        await motor.dispose()

    app = FastAPI(title=config.service_name, version="1.0.0", lifespan=lifespan)
    instrumentar(app)
    app.include_router(rutas.router)
    app.include_router(rutas_clientes.router)

    @app.exception_handler(ErrorDominio)
    async def error_dominio(_: Request, exc: ErrorDominio):
        return JSONResponse(
            status_code=ESTADO_HTTP.get(type(exc), 400),
            content={"codigo": exc.codigo, "mensaje": exc.mensaje},
        )

    return app


app = crear_app()
