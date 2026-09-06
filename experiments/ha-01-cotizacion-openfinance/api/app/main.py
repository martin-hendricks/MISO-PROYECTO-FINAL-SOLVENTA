from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.responses import ORJSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from . import adaptador_of
from .cache import close_cache, init_cache
from .config import settings
from .db import close_pool, init_pool
from .metrics import REQUEST_LATENCY
from .models import OfertaSeguro
from .strategies import arm_a, arm_b, arm_c

STRATEGIES = {
    "A": arm_a.resolver_oferta,
    "B": arm_b.resolver_oferta,
    "C": arm_c.resolver_oferta,
    "C_PRIME": arm_c.resolver_oferta_coalescida,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await init_cache()
    await adaptador_of.init_adapter()
    yield
    await adaptador_of.close_adapter()
    await close_pool()
    await close_cache()


app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)


@app.get("/health")
async def health():
    return {"status": "ok", "arm": settings.read_strategy}


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/cotizaciones/{cliente_id}", response_model=OfertaSeguro)
async def cotizar(cliente_id: int):
    arm = settings.read_strategy
    resolver = STRATEGIES[arm]
    with REQUEST_LATENCY.labels(arm=arm).time():
        prima, origen = await resolver(cliente_id)

    return OfertaSeguro(
        cliente_id=cliente_id,
        prima=prima,
        origen_perfil=origen,
        brazo=arm,
    )
