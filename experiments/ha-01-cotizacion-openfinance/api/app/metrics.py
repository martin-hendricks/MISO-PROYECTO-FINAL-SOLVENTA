from prometheus_client import Counter, Histogram

# Los buckets incluyen 0.225 y 0.475 explícitamente: los umbrales del ASR
# medidos en el servicio (p95 y p99, Anexo B de HA-01). Sin esos buckets,
# Prometheus interpola el percentil y pierde precisión justo donde importa.
REQUEST_LATENCY = Histogram(
    "ha01_cotizacion_latency_seconds",
    "Latencia interna de la cotización embebida",
    labelnames=("arm",),
    buckets=(0.010, 0.025, 0.050, 0.075, 0.100, 0.150,
              0.225, 0.300, 0.475, 0.700, 1.0, 2.5),
)

CACHE_HITS = Counter("ha01_cache_hits_total", "Aciertos de caché de perfil")
CACHE_MISSES = Counter("ha01_cache_misses_total", "Fallos de caché de perfil")

PROVIDER_CALLS = Counter(
    "ha01_provider_calls_total", "Invocaciones al proveedor de Open Finance",
    labelnames=("outcome",),  # success | timeout | error | circuit_open
)

FALLBACK_RESPONSES = Counter(
    "ha01_fallback_responses_total",
    "Respuestas resueltas con último valor conocido o valor por defecto",
    labelnames=("origin",),  # stale_cache | default_value
)

CIRCUIT_STATE = Counter(
    "ha01_circuit_transitions_total", "Transiciones de estado del interruptor de circuito",
    labelnames=("to_state",),  # open | closed | half_open
)

SHED_REQUESTS = Counter(
    "ha01_shed_requests_total", "Peticiones sacrificadas por el interruptor abierto"
)
