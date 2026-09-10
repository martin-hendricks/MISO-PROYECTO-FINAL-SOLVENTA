"""Los cuatro brazos del experimento, sobre el mismo binario.

La estrategia de resolucion del perfil es la UNICA variable que cambia
entre corridas del bloque 1. Todo lo demas -motor de tarifa, serializacion,
forma de la respuesta- es identico por construccion.

Cada brazo devuelve una `Resolucion`: el perfil y, por separado, el origen
con que se resolvio ESTA peticion. El origen no se lee del blob almacenado
porque un perfil escrito por el adaptador y leido despues desde la cache es
un acierto de cache, no una invocacion.
"""
import asyncio
from dataclasses import dataclass

from . import config
from .cache import edad_segundos
from .metrics import (
    CACHE_HITS,
    CACHE_MISSES,
    COALESCIDAS,
    PERFIL_ORIGEN,
    REFRESCOS,
)

BUDGET = config.DEPENDENCY_BUDGET_S
TTL = config.PROFILE_TTL_SECONDS
MAX_AGE = config.PROFILE_MAX_AGE_SECONDS

# Valores deliberadamente conservadores: representan un cliente
# promedio-bajo, de modo que la prima resultante sea prudente y no
# favorable. Es una decision actuarial, no tecnica.
PERFIL_DEFECTO = {
    "customer_id": None,
    "score_pago": 0.80,
    "carga_financiera": 0.45,
    "estabilidad_ingreso": 0.60,
    "antiguedad_meses": 24,
    "obtenido_en": None,
}


@dataclass(slots=True)
class Resolucion:
    perfil: dict
    origen: str              # cache | open_finance | fallback | default
    # Antiguedad del dato con que se tarifico. `None` cuando NO APLICA: el
    # perfil por defecto no tiene marca de tiempo, y anotarlo con MAX_AGE
    # inflaria el p95 de frescura justo en las corridas donde mas defaults
    # hay, que son las que el experimento quiere caracterizar.
    edad_s: float | None

    @property
    def degradada(self) -> bool:
        return self.origen in ("fallback", "default")


def _res(perfil: dict, origen: str, edad: float | None = None) -> Resolucion:
    PERFIL_ORIGEN.labels(origen=origen).inc()
    if origen == "default":
        return Resolucion(perfil, origen, None)
    if edad is None:
        edad = 0.0 if origen == "open_finance" else edad_segundos(perfil)
    if edad == float("inf"):
        edad = None
    return Resolucion(perfil, origen, edad)


def _respaldo(previo: dict | None) -> Resolucion:
    """Ultimo valor conocido si sigue siendo utilizable; si no, por defecto."""
    if previo is not None:
        edad = edad_segundos(previo)
        if edad <= MAX_AGE:
            return _res(previo, "fallback", edad)
    return _res(PERFIL_DEFECTO, "default")


# ---------------------------------------------------------------------
# A — invocacion bloqueante sin cache. Linea base.
# ---------------------------------------------------------------------
async def brazo_directo(ctx, customer_id: str) -> Resolucion:
    perfil = await ctx.adaptador.obtener_perfil(customer_id)
    if perfil is None:
        return _res(PERFIL_DEFECTO, "default")
    return _res(perfil, "open_finance")


# ---------------------------------------------------------------------
# B — cache-aside clasico: el fallo ESPERA al proveedor.
# ---------------------------------------------------------------------
async def brazo_cache_bloqueante(ctx, customer_id: str) -> Resolucion:
    previo = await ctx.cache.leer(customer_id)
    if previo is not None:
        edad = edad_segundos(previo)
        if edad <= TTL:
            CACHE_HITS.inc()
            return _res(previo, "cache", edad)
    CACHE_MISSES.inc()

    fresco = await ctx.adaptador.obtener_perfil(customer_id)   # <-- bloquea
    if fresco is not None:
        await ctx.cache.escribir(customer_id, fresco)
        return _res(fresco, "open_finance")
    return _respaldo(previo)


# ---------------------------------------------------------------------
# C — el diseno propuesto: la respuesta NUNCA espera al proveedor mas alla
#     del presupuesto por dependencia.
# ---------------------------------------------------------------------
async def brazo_oportunista(ctx, customer_id: str) -> Resolucion:
    previo = await ctx.cache.leer(customer_id)
    if previo is not None:
        edad = edad_segundos(previo)
        if edad <= TTL:
            CACHE_HITS.inc()
            return _res(previo, "cache", edad)
    CACHE_MISSES.inc()

    tarea = ctx.lanzar_refresco(customer_id)
    if tarea is None:                       # cota de refrescos alcanzada
        return _respaldo(previo)

    try:
        # Se espera SOLO el presupuesto. `shield` es lo que impide que
        # `wait_for` cancele la tarea al vencer: sin el, el brazo C se
        # convertiria en un brazo B con timeout mas corto.
        fresco = await asyncio.wait_for(asyncio.shield(tarea), timeout=BUDGET)
        if fresco is not None:
            return _res(fresco, "open_finance")
    except asyncio.TimeoutError:
        REFRESCOS.labels(resultado="continua_en_segundo_plano").inc()
        # NO se cancela: la tarea corre hasta el timeout duro del adaptador
        # y repuebla la cache si alcanza a completarse. Ese es el sentido de
        # "actualizacion oportunista" de la wiki, §1.2.4.

    return _respaldo(previo)


# ---------------------------------------------------------------------
# C' — igual que C, pero una sola invocacion en vuelo por clave.
# ---------------------------------------------------------------------
async def brazo_singleflight(ctx, customer_id: str) -> Resolucion:
    previo = await ctx.cache.leer(customer_id)
    if previo is not None:
        edad = edad_segundos(previo)
        if edad <= TTL:
            CACHE_HITS.inc()
            return _res(previo, "cache", edad)
    CACHE_MISSES.inc()

    tarea = ctx.en_vuelo.get(customer_id)
    if tarea is None:
        tarea = ctx.lanzar_refresco(customer_id, clave_coalescencia=customer_id)
        if tarea is None:
            return _respaldo(previo)
    else:
        COALESCIDAS.inc()

    try:
        fresco = await asyncio.wait_for(asyncio.shield(tarea), timeout=BUDGET)
        if fresco is not None:
            return _res(fresco, "open_finance")
    except asyncio.TimeoutError:
        REFRESCOS.labels(resultado="continua_en_segundo_plano").inc()

    return _respaldo(previo)


ESTRATEGIAS = {
    "direct": brazo_directo,
    "cache_blocking": brazo_cache_bloqueante,
    "cache_opportunistic": brazo_oportunista,
    "cache_singleflight": brazo_singleflight,
}

USA_CACHE = {
    "direct": False,
    "cache_blocking": True,
    "cache_opportunistic": True,
    "cache_singleflight": True,
}
