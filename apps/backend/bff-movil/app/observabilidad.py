import time

from fastapi import FastAPI, Request
from prometheus_client import CONTENT_TYPE_LATEST, Histogram, generate_latest
from starlette.responses import Response

LATENCIA = Histogram(
    "http_request_duration_seconds",
    "Latencia de peticiones HTTP",
    ["method", "route", "status"],
    buckets=(0.025, 0.05, 0.1, 0.15, 0.25, 0.4, 0.8, 1.5, 3.0, 5.0),
)


def instrumentar(app: FastAPI) -> None:
    @app.middleware("http")
    async def latencia(request: Request, call_next):
        inicio = time.perf_counter()
        respuesta = await call_next(request)
        ruta = request.scope.get("route")
        LATENCIA.labels(
            request.method, getattr(ruta, "path", "sin_ruta"), str(respuesta.status_code)
        ).observe(time.perf_counter() - inicio)
        return respuesta

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
