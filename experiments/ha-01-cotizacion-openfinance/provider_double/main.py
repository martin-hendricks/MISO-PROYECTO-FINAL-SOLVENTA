import asyncio
import os
import time

import numpy as np
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

app = FastAPI(default_response_class=ORJSONResponse)

MEDIAN_MS = float(os.environ.get("PROVIDER_LATENCY_MEDIAN_MS", "80"))
SIGMA = float(os.environ.get("PROVIDER_LATENCY_SIGMA", "0.5"))
SEED = int(os.environ.get("PROVIDER_SEED", "42"))

# Semilla fija para que dos repeticiones bajo la misma configuración sean
# comparables: el punto de sensibilidad es el estado del proveedor, no el
# ruido del generador aleatorio.
_rng = np.random.default_rng(SEED)


def _sample_latency_seconds() -> float:
    # Log-normal con mediana MEDIAN_MS y cola larga, como especifica el
    # diseño del experimento (Anexo A): no un valor constante.
    mu = np.log(MEDIAN_MS)
    ms = _rng.lognormal(mean=mu, sigma=SIGMA)
    return ms / 1000.0


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/perfil/{cliente_id}")
async def perfil_open_finance(cliente_id: int):
    delay = _sample_latency_seconds()
    await asyncio.sleep(delay)

    # Forma real del contrato de Open Finance (señales financieras), para
    # que el costo de deserialización en el adaptador sea representativo.
    return {
        "cliente_id": cliente_id,
        "endeudamiento": round(0.1 + (cliente_id % 100) / 200, 4),
        "capacidad_pago": round(1_000_000 + (cliente_id % 500) * 15_000, 2),
        "score_comportamiento_pago": 300 + (cliente_id % 700),
        "fuente": "open_finance_sandbox",
        "generado_en": time.time(),
    }
