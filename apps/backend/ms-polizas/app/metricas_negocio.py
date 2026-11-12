"""Métricas de negocio del ciclo de vida de pólizas, separadas de
observabilidad.py (middleware HTTP genérico). Mismo patrón que
experiments/ha-01-cotizacion-openfinance/api/app/metrics.py."""

from prometheus_client import Counter, Histogram

RENOVACIONES = Counter(
    "solventa_polizas_renovaciones_total",
    "Renovaciones de poliza por resultado",
    ["resultado"],  # exitosa | rechazada
)

CANCELACIONES = Counter(
    "solventa_polizas_cancelaciones_total",
    "Cancelaciones de poliza",
)

AVISOS_VENCIMIENTO_JOB_LATENCIA = Histogram(
    "solventa_avisos_vencimiento_job_latency_seconds",
    "Latencia del job periodico de avisos de vencimiento (HU-67)",
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

EMISION_LATENCIA = Histogram(
    "solventa_emision_latency_seconds",
    "Latencia del flujo de emision (verificar suscripcion/cobro + firma + numerar poliza)",
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 3.5, 5.0, 10.0),
)
