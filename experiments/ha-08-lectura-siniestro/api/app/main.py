from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import ORJSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from .config import settings
from .db import init_pool, close_pool
from .cache import init_cache, close_cache
from .metrics import REQUEST_LATENCY
from .models import EstadoSiniestro
from .strategies import arm_a, arm_b, arm_c

STRATEGIES = {"A": arm_a.get_estado, "B": arm_b.get_estado, "C": arm_c.get_estado}

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool()
    await init_cache()
    yield
    await close_pool()
    await close_cache()

app = FastAPI(lifespan=lifespan, default_response_class=ORJSONResponse)

@app.get("/health")
async def health():
    return {"status": "ok", "arm": settings.read_strategy}

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/siniestros/{siniestro_id}/estado", response_model=EstadoSiniestro)
async def estado_siniestro(siniestro_id: int):
    arm = settings.read_strategy
    with REQUEST_LATENCY.labels(arm=arm).time():
        if arm == "C_PRIME":
            raw = await arm_c.get_estado_raw(siniestro_id)
            if raw is None:
                raise HTTPException(404, "Siniestro no encontrado")
            return Response(content=raw, media_type="application/json")

        data = await STRATEGIES[arm](siniestro_id)
        if data is None:
            raise HTTPException(404, "Siniestro no encontrado")
        return data
