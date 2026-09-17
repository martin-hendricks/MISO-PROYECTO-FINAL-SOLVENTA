"""Doble del proveedor de Open Finance — INSTRUMENTACION, no arquitectura.

Sustituye al «External» :OpenFinance del modelo de componentes. Devuelve la
FORMA REAL del contrato para que el costo de deserializar y mapear al
canonico en :AdaptadorOF sea representativo: simplificarlo falsearia el
brazo A, que es la linea base contra la que se mide todo.

Tres propiedades que debe cumplir:

1. DETERMINISTA. La latencia se deriva por hash de (semilla, customer_id),
   no de un generador global. Un `random.Random` compartido entre corrutinas
   produce secuencias que dependen del entrelazado, y dos repeticiones con
   la misma semilla dejarian de ser comparables bajo concurrencia.
   EXCEPCION deliberada: la decision de FALLO se deriva de un contador de
   peticion, no del customer_id. Atarla al cliente convertia el estado
   `intermitente` en un subconjunto fijo de clientes rotos en vez de un
   proveedor que falla a veces (ver «Fallas intermitentes»).
2. SIN ESTADO. No guarda nada entre peticiones: cualquier acumulacion
   introduciria deriva a lo largo de la ventana de medicion.
3. NUNCA SATURADO. Se le asignan mas recursos que a la API a proposito.
   `verify_provider.sh` lo comprueba antes de cada bloque.

Sobre los percentiles: la log-normal se ajusta con p50 y p95, que la
determinan por completo. P99 NO se controla -con 60/110 el p99 realizado es
~141 ms- y solo se usa como cota superior de la cola.
"""
import hashlib
import itertools
import math
import os
import statistics
from datetime import datetime, timezone

from fastapi import FastAPI, Response
from fastapi.responses import ORJSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(default_response_class=ORJSONResponse)

SERVED = Counter("ha01_provider_requests", "Peticiones atendidas por el doble")
ERRORES = Counter("ha01_provider_errors", "Respuestas de error del doble", ["codigo"])
LAT = Histogram(
    "ha01_provider_latency_seconds",
    "Latencia de aplicacion inyectada por el doble",
    buckets=(0.02, 0.04, 0.06, 0.08, 0.11, 0.14, 0.18, 0.25, 0.35, 0.6, 1.0),
)

P50 = int(os.environ.get("PROVIDER_LATENCY_P50_MS", "60")) / 1000
P95 = int(os.environ.get("PROVIDER_LATENCY_P95_MS", "110")) / 1000
P99_CAP = int(os.environ.get("PROVIDER_LATENCY_P99_MS", "180")) / 1000
ERROR_RATE = float(os.environ.get("PROVIDER_ERROR_RATE", "0"))
SEED = os.environ.get("PROVIDER_SEED", "42")

MU = math.log(P50)
SIGMA = (math.log(P95) - MU) / statistics.NormalDist().inv_cdf(0.95)
TECHO = P99_CAP * 6
_NORMAL = statistics.NormalDist()


def _uniforme_cliente(customer_id: str) -> float:
    """Uniforme en (0,1) derivada de la semilla y el cliente."""
    d = hashlib.blake2b(f"{SEED}:{customer_id}".encode(), digest_size=16).digest()
    a = int.from_bytes(d[:8], "big") / 2**64
    return min(max(a, 1e-9), 1 - 1e-9)


# Secuencia de peticion: sostiene la uniforme del fallo, que NO puede
# derivarse del customer_id (ver «Fallas intermitentes»).
_SECUENCIA = itertools.count()


def _uniforme_peticion() -> float:
    """Uniforme en (0,1) por PETICION, independiente del cliente."""
    n = next(_SECUENCIA)
    d = hashlib.blake2b(f"{SEED}:peticion:{n}".encode(), digest_size=8).digest()
    return int.from_bytes(d, "big") / 2**64


def muestrear_latencia(customer_id: str) -> float:
    u = _uniforme_cliente(customer_id)
    # Cota superior para que el doble no se vuelva el caso patologico:
    # el objeto de estudio es el diseno, no un proveedor imposible.
    return min(math.exp(MU + SIGMA * _NORMAL.inv_cdf(u)), TECHO)


# --- Fallas intermitentes ---------------------------------------------
# Fraccion de peticiones que se cuelgan mas alla del timeout duro del
# adaptador. Modela el proveedor que falla A VECES, que es el caso en el que
# las dos politicas del interruptor divergen: con 30 % de fallos, ni diez
# fallos consecutivos ni una tasa del 50 % sobre la ventana se alcanzan, asi
# que el interruptor NO abre y el pool se llena con llamadas colgadas.
#
# La decision se toma POR PETICION, no por cliente. Derivarla de la misma
# uniforme que la latencia -hash de (semilla, customer_id)- convertia este
# estado en «un subconjunto fijo del 30 % de clientes que falla SIEMPRE»: la
# clave de esos clientes no se repuebla nunca y los fallos se concentran en
# una parte fija del espacio de claves. Es un modo de falla distinto del que
# se quiere modelar, y el razonamiento de por que el interruptor no abre
# depende del ENTRELAZADO de fallos y aciertos, que difiere entre ambos.
#
# Se usa un contador de peticion y no `random()` para no perder la
# reproducibilidad dada la secuencia de llegada. La LATENCIA sigue siendo
# determinista por cliente (propiedad 1 del encabezado): lo que se desacopla
# aqui es unicamente la decision de fallo.
#
# Se conmuta en caliente por `states.sh`, sin reiniciar, porque el protocolo
# cambia de estado a mitad de corrida.
FALLO_FRACCION = 0.0
CUELGUE_S = float(os.environ.get("PROVIDER_CUELGUE_S", "2.0"))
COLGADAS = Counter("ha01_provider_colgadas", "Peticiones colgadas a proposito")


@app.post("/modo")
def modo(fallo_fraccion: float = 0.0):
    global FALLO_FRACCION
    FALLO_FRACCION = max(0.0, min(1.0, fallo_fraccion))
    return {"fallo_fraccion": FALLO_FRACCION, "cuelgue_s": CUELGUE_S}


@app.get("/modo")
def ver_modo():
    return {"fallo_fraccion": FALLO_FRACCION, "cuelgue_s": CUELGUE_S}


@app.get("/open-finance/v1/customers/{customer_id}/financial-data")
async def datos_financieros(customer_id: str):
    import asyncio

    espera = muestrear_latencia(customer_id)
    w = _uniforme_peticion()
    if FALLO_FRACCION and w < FALLO_FRACCION:
        # Se cuelga mas alla del timeout duro: el adaptador abandonara solo.
        COLGADAS.inc()
        await asyncio.sleep(CUELGUE_S)
        return Response(status_code=504)
    await asyncio.sleep(espera)
    LAT.observe(espera)
    SERVED.inc()

    if ERROR_RATE and w < ERROR_RATE:
        ERRORES.labels(codigo="503").inc()
        return Response(status_code=503)

    return {
        "consent_id": f"cns_{customer_id[-6:]}",
        "customer_id": customer_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accounts": [
            {"account_id": "acc_1", "type": "CHECKING", "currency": "COP",
             "balance": 4820000, "opened_at": "2019-03-02"}
        ],
        "income": {"monthly_avg": 6200000, "stability_index": 0.87,
                   "months_observed": 24},
        "obligations": [
            {"product": "CREDIT_CARD", "outstanding": 2100000,
             "utilization": 0.31, "days_past_due_12m": 0}
        ],
        "payment_behavior": {"on_time_ratio_12m": 0.98, "max_dpd_12m": 3,
                             "inquiries_6m": 2},
    }


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/perfil-latencia")
def perfil_latencia():
    """Percentiles REALIZADOS de la distribucion configurada.

    Se consulta en la verificacion de sanidad. El p99 configurado no se
    controla: la log-normal queda determinada por p50 y p95.
    """
    def q(p: float) -> float:
        return min(math.exp(MU + SIGMA * _NORMAL.inv_cdf(p)), TECHO)

    return {
        "configurado_ms": {"p50": P50 * 1000, "p95": P95 * 1000,
                           "p99_solo_cota": P99_CAP * 1000},
        "realizado_ms": {"p50": round(q(0.5) * 1000, 1),
                         "p95": round(q(0.95) * 1000, 1),
                         "p99": round(q(0.99) * 1000, 1),
                         "techo": round(TECHO * 1000, 1)},
        "mu": MU, "sigma": SIGMA, "seed": SEED,
    }


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
