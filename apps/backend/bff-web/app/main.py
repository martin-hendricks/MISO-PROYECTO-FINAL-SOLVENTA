import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .clients.base import RechazoDelNucleo, RecursoNoEncontrado, ServicioNoDisponible
from .config import Settings
from .routers import asesor, cliente, operador, registro, sesion

logger = logging.getLogger(__name__)

config = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # bff-web habla con los microservicios de núcleo por red interna del
    # cluster (Service de Kubernetes) -- nunca otra vez a través del
    # ALB/API Gateway. Un AsyncClient por microservicio, cada uno con su
    # propia base_url/timeout (ver app/config.py).
    async with (
        httpx.AsyncClient(base_url=config.ms_cotizacion_url, timeout=config.timeout_nucleo_s) as http_cotizacion,
        httpx.AsyncClient(base_url=config.ms_pagos_url, timeout=config.timeout_nucleo_s) as http_pagos,
        httpx.AsyncClient(base_url=config.ms_polizas_url, timeout=config.timeout_nucleo_s) as http_polizas,
        httpx.AsyncClient(
            base_url=config.ms_perfilamiento_url, timeout=config.timeout_nucleo_s
        ) as http_perfilamiento,
        httpx.AsyncClient(base_url=config.ms_siniestros_url, timeout=config.timeout_nucleo_s) as http_siniestros,
        httpx.AsyncClient(base_url=config.ms_suscripcion_url, timeout=config.timeout_nucleo_s) as http_suscripcion,
        httpx.AsyncClient(base_url=config.ms_identidad_url, timeout=config.timeout_nucleo_s) as http_identidad,
    ):
        app.state.http_ms_cotizacion = http_cotizacion
        app.state.http_ms_pagos = http_pagos
        app.state.http_ms_polizas = http_polizas
        app.state.http_ms_perfilamiento = http_perfilamiento
        app.state.http_ms_siniestros = http_siniestros
        app.state.http_ms_suscripcion = http_suscripcion
        app.state.http_ms_identidad = http_identidad
        yield


app = FastAPI(title="bff-web", lifespan=lifespan)
app.state.config = config

# El API Gateway (infra/terraform/modules/edge) ya agrega headers CORS a la
# respuesta, pero no responde el preflight por sí mismo: un OPTIONS que
# llega hasta aquí sin este middleware recibe 405 Method Not Allowed de
# FastAPI (solo hay handlers POST/GET registrados), y el navegador rechaza
# el preflight por no tener status 2xx aunque los headers CORS ya estén
# puestos (confirmado contra el API Gateway real). CORSMiddleware es quien
# debe responder el OPTIONS -- el navegador habla con este servicio, no con
# el API Gateway, en lo que a CORS respecta.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prefijo de versión centralizado: cada router sigue declarando su propio
# prefix (/cliente, /asesor, etc.) sin "/v1" -- así el prefijo de versión no
# se repite en cada archivo ni se puede olvidar en uno nuevo.
app.include_router(sesion.router, prefix="/v1")
app.include_router(registro.router, prefix="/v1")
app.include_router(cliente.router, prefix="/v1")
app.include_router(asesor.router, prefix="/v1")
app.include_router(operador.router, prefix="/v1")


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


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
