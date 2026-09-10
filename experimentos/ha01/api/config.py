"""Lectura centralizada de la configuracion del experimento.

Un solo punto de lectura de variables de entorno: si un brazo leyera un
parametro distinto del que lee otro, la comparacion entre brazos dejaria
de ser valida y el defecto seria practicamente invisible en los datos.
"""
import os


def _int(nombre: str, defecto: str) -> int:
    return int(os.environ.get(nombre, defecto))


def _float(nombre: str, defecto: str) -> float:
    return float(os.environ.get(nombre, defecto))


# --- Brazo -----------------------------------------------------------
QUOTE_STRATEGY = os.environ.get("QUOTE_STRATEGY", "cache_opportunistic")

# --- Presupuestos (EC-LAT-07 / EC-LAT-08) ----------------------------
DEPENDENCY_BUDGET_S = _int("DEPENDENCY_BUDGET_MS", "120") / 1000
ADAPTER_HARD_TIMEOUT_S = _int("ADAPTER_HARD_TIMEOUT_MS", "700") / 1000
ADAPTER_CONNECT_TIMEOUT_S = _int("ADAPTER_CONNECT_TIMEOUT_MS", "200") / 1000

# --- Interruptor -----------------------------------------------------
BREAKER_POLICY = os.environ.get("BREAKER_POLICY", "rate")
BREAKER_FAILURE_THRESHOLD = _int("BREAKER_FAILURE_THRESHOLD", "10")
BREAKER_FAILURE_RATE = _float("BREAKER_FAILURE_RATE", "0.5")
BREAKER_WINDOW_SECONDS = _float("BREAKER_WINDOW_SECONDS", "10")
BREAKER_MIN_SAMPLES = _int("BREAKER_MIN_SAMPLES", "5")
BREAKER_OPEN_SECONDS = _float("BREAKER_OPEN_SECONDS", "15")
BREAKER_HALF_OPEN_PROBES = _int("BREAKER_HALF_OPEN_PROBES", "1")

# --- Bulkhead --------------------------------------------------------
ADAPTER_MAX_CONNECTIONS = _int("ADAPTER_MAX_CONNECTIONS", "40")
ADAPTER_MAX_KEEPALIVE = _int("ADAPTER_MAX_KEEPALIVE", "20")
REFRESH_MAX_INFLIGHT = _int("REFRESH_MAX_INFLIGHT", "0")

# --- Cache -----------------------------------------------------------
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379/0")
PROFILE_TTL_SECONDS = _int("PROFILE_TTL_SECONDS", "900")
PROFILE_MAX_AGE_SECONDS = _int("PROFILE_MAX_AGE_SECONDS", "86400")
CACHE_KEY_PREFIX = os.environ.get("CACHE_KEY_PREFIX", "of:perfil:")

# --- Motor de tarifa -------------------------------------------------
RATING_COST_S = _int("RATING_COST_MS", "60") / 1000
RATING_CPU_ITERS = _int("RATING_CPU_ITERS", "1200")

# --- Proveedor -------------------------------------------------------
PROVIDER_BASE_URL = os.environ.get("PROVIDER_BASE_URL", "http://toxiproxy:19000")
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://solventa:solventa@postgres:5432/solventa"
)

# --- Umbrales, solo para exponerlos en /info -------------------------
SLO_P95_MS = _int("SLO_P95_MS", "225")
SLO_P99_MS = _int("SLO_P99_MS", "475")
