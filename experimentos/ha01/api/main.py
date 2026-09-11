"""`:MsCotizacion` — recurso de cotizacion embebida y seleccion de brazo."""
import asyncio
import time
from contextlib import asynccontextmanager

import orjson
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import config
from .adapter import AdaptadorOF
from .cache import CacheOF
from .context import Contexto
from .metrics import (
    COTIZACIONES,
    COTIZACIONES_ERROR,
    DEGRADADAS,
    LOOP_LAG,
    PERFIL_EDAD,
    QUOTE_LAT,
)
from .rating import REGLAS_FALLBACK, MotorTarifa
from .strategies import ESTRATEGIAS, USA_CACHE

ESTRATEGIA = ESTRATEGIAS[config.QUOTE_STRATEGY]
PERIODO_SONDA = 0.1


async def _sonda_bucle() -> None:
    """Detector de interferencia: mide cuanto se retrasa el bucle de eventos.

    Diez despertares por segundo frente a 100-200 cotizaciones por segundo:
    su propio costo es despreciable.
    """
    loop = asyncio.get_running_loop()
    while True:
        t0 = loop.time()
        await asyncio.sleep(PERIODO_SONDA)
        LOOP_LAG.observe(max(0.0, loop.time() - t0 - PERIODO_SONDA))


@asynccontextmanager
async def lifespan(app: FastAPI):
    adaptador = AdaptadorOF()
    cache = CacheOF()
    try:
        rating = await MotorTarifa.desde_postgres()
    except Exception:
        # El catalogo de reglas no es la variable bajo estudio; si Postgres
        # no esta, se arranca con el conjunto de respaldo y se declara en
        # /info para que la corrida no se de por valida en silencio.
        rating = MotorTarifa(dict(REGLAS_FALLBACK))
        app.state.reglas_desde_bd = False
    else:
        app.state.reglas_desde_bd = True

    app.state.ctx = Contexto(adaptador, cache, rating)
    sonda = asyncio.create_task(_sonda_bucle())
    try:
        yield
    finally:
        sonda.cancel()
        await app.state.ctx.drenar()
        await adaptador.aclose()
        await cache.aclose()


app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)


@app.post("/v1/cotizaciones")
async def cotizar(request: Request):
    inicio = time.perf_counter()
    ctx = request.app.state.ctx
    try:
        payload = orjson.loads(await request.body())
        customer_id = payload["customer_id"]
        producto = payload.get("producto", "VIAJE_BASICO")
    except (orjson.JSONDecodeError, KeyError, TypeError):
        COTIZACIONES_ERROR.labels(motivo="payload").inc()
        return ORJSONResponse({"error": "payload invalido"}, status_code=400)

    try:
        r = await ESTRATEGIA(ctx, customer_id)
        prima = await ctx.rating.calcular(r.perfil, producto, r.degradada)
    except Exception:
        COTIZACIONES_ERROR.labels(motivo="interno").inc()
        QUOTE_LAT.labels(origen="error").observe(time.perf_counter() - inicio)
        return ORJSONResponse({"error": "error interno"}, status_code=500)

    COTIZACIONES.inc()
    if r.degradada:
        DEGRADADAS.inc()
    # Solo se observa la edad cuando el dato TIENE edad. La proporcion sin
    # edad es exactamente `ha01_perfil_origen_total{origen="default"}`.
    if r.edad_s is not None:
        PERFIL_EDAD.observe(r.edad_s)
    QUOTE_LAT.labels(origen=r.origen).observe(time.perf_counter() - inicio)

    return {
        "cotizacion_id": f"cot_{customer_id[-6:]}",
        "prima": prima,
        "moneda": "COP",
        "perfil_origen": r.origen,
        "perfil_edad_segundos": None if r.edad_s is None else round(r.edad_s, 3),
        "degradada": r.degradada,
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health(request: Request):
    return {"ok": await request.app.state.ctx.cache.ping()}


@app.get("/info")
async def info(request: Request):
    """Configuracion efectiva de la corrida.

    `collect_results.sh` la guarda junto a las metricas: sin ella, un
    resultado no es reproducible ni auditable seis semanas despues.
    """
    ctx = request.app.state.ctx
    return {
        "brazo": config.QUOTE_STRATEGY,
        "usa_cache": USA_CACHE[config.QUOTE_STRATEGY],
        "presupuesto_dependencia_ms": int(config.DEPENDENCY_BUDGET_S * 1000),
        "timeout_duro_ms": int(config.ADAPTER_HARD_TIMEOUT_S * 1000),
        "slo_servicio_ms": {"p95": config.SLO_P95_MS, "p99": config.SLO_P99_MS},
        "interruptor": ctx.adaptador.interruptor.snapshot(),
        "pool": {
            "max_connections": config.ADAPTER_MAX_CONNECTIONS,
            "max_keepalive": config.ADAPTER_MAX_KEEPALIVE,
        },
        "cache": {
            "ttl_s": config.PROFILE_TTL_SECONDS,
            "max_age_s": config.PROFILE_MAX_AGE_SECONDS,
            **(await ctx.cache.info_memoria()),
        },
        "rating_cost_ms": int(config.RATING_COST_S * 1000),
        "reglas_desde_bd": getattr(request.app.state, "reglas_desde_bd", None),
        "refrescos_activos": ctx.refrescos_activos,
        "provider_base_url": config.PROVIDER_BASE_URL,
    }
