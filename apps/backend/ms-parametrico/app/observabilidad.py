import time
import uuid

from fastapi import FastAPI, Request, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, Histogram, generate_latest

LATENCIA = Histogram(
    "http_request_duration_seconds",
    "Latencia de peticiones HTTP",
    ["method", "route", "status"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
)
CABECERA_CORRELACION = "X-Correlation-Id"


def instrumentar(app: FastAPI) -> None:
    @app.middleware("http")
    async def correlacion_y_latencia(request: Request, call_next):
        correlacion = request.headers.get(CABECERA_CORRELACION) or str(uuid.uuid4())
        request.state.correlacion = correlacion
        inicio = time.perf_counter()
        respuesta = await call_next(request)
        ruta = request.scope.get("route")
        LATENCIA.labels(
            request.method, getattr(ruta, "path", "sin_ruta"), str(respuesta.status_code)
        ).observe(time.perf_counter() - inicio)
        respuesta.headers[CABECERA_CORRELACION] = correlacion
        return respuesta

    @app.get("/health/live", include_in_schema=False)
    async def health_live():
        return {"status": "ok"}

    @app.get("/health/ready", include_in_schema=False)
    async def health_ready(request: Request, response: Response):
        if request.app.state.publicador.listo():
            return {"status": "ok"}
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable"}

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
