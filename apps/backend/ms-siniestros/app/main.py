import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import rutas, rutas_avisos
from app.application.worker import ciclo_de_evaluacion
from app.config import Settings
from app.domain.errores import ErrorDominio, NoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.infrastructure.evidencias import AlmacenEvidenciasEnMemoria, AlmacenEvidenciasS3
from app.infrastructure.pagos import AdaptadorDesembolsoStub
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo
from app.observabilidad import instrumentar
from app.ports.evidencias import ErrorAlmacenEvidencias

ESTADO_HTTP = {NoEncontrado: 404, TransicionInvalida: 409, ReglaDeNegocioViolada: 422}

log = logging.getLogger(__name__)


def estado_http(exc: ErrorDominio) -> int:
    return next((estado for tipo, estado in ESTADO_HTTP.items() if isinstance(exc, tipo)), 400)


def crear_almacen_evidencias(config: Settings):
    if not config.s3_evidencias_bucket:
        log.warning("S3_EVIDENCIAS_BUCKET vacío: la evidencia se guarda en memoria (solo desarrollo)")
        return AlmacenEvidenciasEnMemoria()
    return AlmacenEvidenciasS3(
        bucket=config.s3_evidencias_bucket,
        region=config.aws_region,
        endpoint_url=config.s3_endpoint_url,
        endpoint_publico=config.s3_endpoint_publico,
        access_key=config.s3_access_key,
        secret_key=config.s3_secret_key,
        kms_key_id=config.s3_kms_key_id,
    )


def crear_app(config: Settings | None = None) -> FastAPI:
    config = config or Settings()
    logging.basicConfig(level=config.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        motor = crear_motor(config)
        app.state.motor = motor
        app.state.fabrica_uow = fabrica_unidad_de_trabajo(motor)
        app.state.adaptador_desembolso = AdaptadorDesembolsoStub()
        almacen = crear_almacen_evidencias(config)
        if config.s3_crear_bucket and isinstance(almacen, AlmacenEvidenciasS3):
            await almacen.asegurar_bucket()
        app.state.almacen_evidencias = almacen

        detener = asyncio.Event()
        tarea = None
        if config.worker_evaluacion_habilitado:
            tarea = asyncio.create_task(
                ciclo_de_evaluacion(
                    app.state.fabrica_uow, app.state.adaptador_desembolso, config.worker_intervalo_segundos, detener
                )
            )
        yield
        detener.set()
        if tarea is not None:
            with suppress(asyncio.CancelledError):
                await tarea
        await motor.dispose()

    app = FastAPI(title=config.service_name, version="1.1.0", lifespan=lifespan)
    app.state.config = config
    instrumentar(app)
    app.include_router(rutas.router)
    app.include_router(rutas_avisos.router)

    @app.exception_handler(ErrorDominio)
    async def error_dominio(_: Request, exc: ErrorDominio):
        return JSONResponse(
            status_code=estado_http(exc),
            content={"codigo": exc.codigo, "mensaje": exc.mensaje},
        )

    @app.exception_handler(ErrorAlmacenEvidencias)
    async def error_almacen(_: Request, exc: ErrorAlmacenEvidencias):
        # §6.3: el aviso no se registra a medias; el canal puede reintentar con la misma clave.
        return JSONResponse(status_code=503, content={"codigo": "evidencia_no_disponible", "mensaje": str(exc)})

    return app


app = crear_app()
