from prometheus_client import Counter, Histogram

# Los buckets incluyen 0.150 explícitamente, el umbral del ASR EC-LAT-11.
# Sin ese bucket, el p95 calculado por Prometheus se interpola entre 0.100
# y 0.250 y pierde precisión justo donde importa.
REQUEST_LATENCY = Histogram(
    "ha08_read_latency_seconds",
    "Latencia interna de la consulta de estado de siniestro",
    labelnames=("arm",),
    buckets=(0.005, 0.010, 0.025, 0.050, 0.075, 0.100,
             0.150, 0.250, 0.500, 1.0, 2.5),
)
CACHE_HITS = Counter("ha08_cache_hits_total", "Aciertos de caché")
CACHE_MISSES = Counter("ha08_cache_misses_total", "Fallos de caché")
