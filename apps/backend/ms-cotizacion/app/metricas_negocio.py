"""Métricas de negocio de cotización/emisión, separadas de observabilidad.py
(que es el middleware HTTP genérico, igual en todos los microservicios).
Mismo patrón que experiments/ha-01-cotizacion-openfinance/api/app/metrics.py:
Counter/Histogram de prometheus_client, prefijo por dominio en vez de por
experimento (solventa_ en vez de ha01_)."""

from prometheus_client import Counter, Histogram

COTIZACION_LATENCIA = Histogram(
    "solventa_cotizacion_latency_seconds",
    "Latencia del flujo de cotizacion embebida (recibir solicitud + calcular prima + oferta)",
    buckets=(0.05, 0.1, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.5, 5.0),
)

OFERTAS = Counter(
    "solventa_ofertas_total",
    "Ofertas de cotizacion por resultado",
    ["resultado"],  # aceptada | creada
)
