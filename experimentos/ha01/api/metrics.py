"""Definicion central de las metricas Prometheus del experimento.

Todas viven aqui y en ningun otro lado: una metrica declarada dos veces
en modulos distintos rompe el registro por defecto de prometheus_client
y deja la corrida sin instrumentacion justo donde mas hace falta.

IMPORTANTE — un solo worker. Estas metricas viven en el proceso. Con
UVICORN_WORKERS > 1 habria un registro por worker y el scrape caeria en
uno u otro, produciendo contadores que oscilan. Ver README.
"""
from prometheus_client import Counter, Gauge, Histogram

# --- Latencia de la cotizacion ---------------------------------------
# La etiqueta `origen` es la que separa camino caliente / frio / degradado
# dentro de una misma corrida. Es el insumo directo de HD-01.3.
QUOTE_LAT = Histogram(
    "ha01_quote_latency_seconds",
    "Latencia de la cotizacion medida en el servicio",
    ["origen"],
    # Reticula fina alrededor de los valores que el montaje produce de
    # verdad: ~65 ms el camino caliente, ~125-145 ms el frio con proveedor
    # sano, ~180 ms el acotado por el presupuesto (120 + 60 de tarifa), y los
    # dos umbrales del servicio, 225 y 475 ms.
    buckets=(0.02, 0.05, 0.065, 0.08, 0.10, 0.12, 0.14, 0.16, 0.175, 0.19,
             0.205, 0.225, 0.25, 0.30, 0.40, 0.475, 0.55, 0.70, 0.80, 1.0,
             1.5, 2.0),
)

# --- Resolucion del perfil -------------------------------------------
CACHE_HITS = Counter("ha01_cache_hits", "Aciertos de :CacheOF")
CACHE_MISSES = Counter("ha01_cache_misses", "Fallos de :CacheOF")
CACHE_ERRORS = Counter("ha01_cache_errors", "Errores de acceso a :CacheOF")

PERFIL_ORIGEN = Counter(
    "ha01_perfil_origen",
    "Origen del perfil con el que se tarifico",
    ["origen"],  # cache | open_finance | fallback | default
)

PERFIL_EDAD = Histogram(
    "ha01_perfil_edad_seconds",
    "Antiguedad del perfil usado para tarificar. Cuantifica el trade-off "
    "declarado en §2.8 de la wiki.",
    buckets=(0, 1, 5, 30, 60, 300, 900, 1800, 3600, 21600, 86400),
)

# --- Impacto en el socio (criterio de aceptacion de negocio) ---------
# Una cotizacion degradada es la que se resolvio con fallback o default.
# Es el numerador de "proporcion con respaldo" y el que sostiene HD-01.5.
COTIZACIONES = Counter("ha01_cotizaciones", "Cotizaciones atendidas")
DEGRADADAS = Counter(
    "ha01_cotizaciones_degradadas",
    "Cotizaciones resueltas con valor de respaldo o por defecto",
)
COTIZACIONES_ERROR = Counter(
    "ha01_cotizaciones_error", "Cotizaciones que terminaron en error", ["motivo"]
)

# --- Adaptador -------------------------------------------------------
ADAPTER_LAT = Histogram(
    "ha01_adapter_latency_seconds",
    "Latencia de la invocacion al proveedor vista por :AdaptadorOF",
    buckets=(0.02, 0.05, 0.1, 0.12, 0.2, 0.35, 0.5, 0.7, 1.0, 2.0),
)
ADAPTER_INFLIGHT = Gauge(
    "ha01_adapter_inflight",
    "Invocaciones al proveedor en vuelo. Detecta el agotamiento del pool "
    "por llamadas abandonadas — insumo de HD-01.7.",
)
ADAPTER_CALLS = Counter(
    "ha01_adapter_calls",
    "Invocaciones al proveedor por resultado",
    ["resultado"],  # ok | error_5xx | falla_transporte | cortada_por_breaker
)

# --- Metrica separada de "sacrificadas" ------------------------------
# El documento de diseno usaba un solo contador para dos cosas distintas.
# En A y B una llamada fallida equivale a una peticion de usuario con
# latencia inflada; en C el usuario ya recibio respuesta y lo que falla es
# un refresco de fondo. Se separan para que HD-01.5 y HD-01.6 midan el
# impacto real al socio y no la salud interna del adaptador.
LLAMADAS_FALLIDAS = Counter(
    "ha01_llamadas_fallidas_proveedor",
    "Invocaciones al proveedor que consumieron el timeout duro sin servir "
    "para responder. Salud del adaptador, NO impacto al socio.",
)

# --- Interruptor -----------------------------------------------------
BREAKER_STATE = Gauge(
    "ha01_breaker_state", "0 cerrado · 1 semiabierto · 2 abierto"
)
BREAKER_TRANSITIONS = Counter(
    "ha01_breaker_transitions", "Transiciones del interruptor", ["desde", "hacia"]
)
BREAKER_ABIERTO_SEGUNDOS = Gauge(
    "ha01_breaker_abierto_desde_seconds",
    "Marca de tiempo unix de la ultima apertura del interruptor (0 si cerrado)",
)

# --- Refresco oportunista (brazos C y C') ----------------------------
REFRESCOS = Counter(
    "ha01_refrescos",
    "Refrescos en segundo plano por desenlace",
    # continua_en_segundo_plano | completado | fallido | rechazado_por_cota
    ["resultado"],
)
REFRESCOS_ACTIVOS = Gauge(
    "ha01_refrescos_fondo_activos",
    "Tareas de refresco vivas. Debe volver a cero al terminar la ventana; "
    "si no, el brazo C tiene una fuga.",
)
COALESCIDAS = Counter(
    "ha01_coalescidas",
    "Peticiones que se sumaron a una invocacion ya en vuelo — HD-01.7",
)

# --- Detector de interferencia -----------------------------------------
# Una sonda duerme 100 ms en bucle y anota cuanto de mas tardo en despertar.
# Ese retraso es tiempo en que el bucle de eventos no pudo atender a nadie:
# lo produce tanto la carga propia del worker como la competencia por CPU con
# otros procesos del equipo. Sin esta metrica, una corrida contaminada por
# interferencia es indistinguible de una limpia; con ella, cada corrida trae
# su propia prueba.
LOOP_LAG = Histogram(
    "ha01_event_loop_lag_seconds",
    "Retraso del bucle de eventos de la API sobre un sueno de 100 ms",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
