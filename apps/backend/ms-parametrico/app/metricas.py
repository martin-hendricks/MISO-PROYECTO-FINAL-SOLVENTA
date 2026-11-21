from prometheus_client import Counter

EVENTOS = Counter(
    "solventa_telemetria_eventos_total",
    "Eventos de telemetría recibidos por proveedor y resultado de la ingesta",
    ["proveedor", "resultado"],  # aceptado | rechazado | contrapresion | no_disponible
)
