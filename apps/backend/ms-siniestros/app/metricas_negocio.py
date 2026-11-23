"""Métricas de negocio de siniestros parametricos, separadas de
observabilidad.py (middleware HTTP generico). Mismo patron que
experiments/ha-08-lectura-siniestro/api/app/metrics.py (precedente directo:
ha08_read_latency_seconds)."""

from prometheus_client import Counter, Histogram

LATENCIA = Histogram(
    "solventa_siniestros_latency_seconds",
    "Latencia de operaciones sobre siniestros parametricos",
    ["operacion"],  # registro | hasta_pago
    buckets=(0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

RESULTADO = Counter(
    "solventa_siniestros_resultado_total",
    "Siniestros parametricos por resultado de la evaluacion de umbral",
    ["resultado"],  # pagado | no_pagado
)
