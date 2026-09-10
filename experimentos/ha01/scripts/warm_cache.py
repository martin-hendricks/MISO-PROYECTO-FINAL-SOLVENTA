"""Precarga de :CacheOF y control de la tasa de acierto.

La tasa de acierto no se observa: SE CONSTRUYE, y esa construccion tiene
que ser verificable. Se preparan tres pools disjuntos que k6 sortea con las
mismas probabilidades (ver load/k6/claves.js):

  CALIENTE  cli_h*   obtenido_en = ahora            -> edad <= TTL, acierto
  VENCIDO   cli_s*   obtenido_en = ahora - TTL - m  -> TTL < edad <= MAX_AGE,
                                                       fallo que resuelve a
                                                       `fallback`
  FRIO      cli_c*   ausente                        -> fallo que resuelve a
                                                       `default`

Un fallo de cache NO es lo mismo que un dato vencido. El punto de
sensibilidad 3 mide el camino frio -la clave no esta-, y la degradacion
elegante necesita el camino de respaldo -la clave esta pero es vieja-. Si
todos los fallos fueran de un solo tipo, la mitad de la tactica bajo prueba
quedaria sin ejercitar. Por eso hay dos pools de fallo y no uno.

Uso:  python scripts/warm_cache.py [--verificar]
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone

import redis.asyncio as redis

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
PREFIJO = os.environ.get("CACHE_KEY_PREFIX", "of:perfil:")

N_HOT = int(os.environ.get("UNIVERSO_CLIENTES", "50000"))
N_STALE_CFG = int(os.environ.get("POOL_STALE", "100000"))
HIT = float(os.environ.get("TARGET_HIT_RATE", "0.96"))
STALE_FRACTION = float(os.environ.get("MISS_STALE_FRACTION", "0.5"))

# --- dimensionamiento del pool VENCIDO --------------------------------
#
# El pool frio es infinito por construccion (ids aleatorios sobre 10^12), asi
# que no aporta deriva. El vencido no puede serlo: necesita un valor previo
# realmente precargado.
#
# La deriva aparece en las fases SANAS: un refresco con exito convierte una
# clave vencida en fresca, y la proxima vez que salga sorteada sera un acierto
# en vez de un fallo. En puntos porcentuales:
#
#   deriva = (1 - acierto) * fraccion_vencida * (repobladas / POOL_STALE)
#
# Con 100 000 claves, acierto 50 % y 200 sol/s durante los 240 s sanos del
# protocolo real, eso da 3 puntos: el doble de la tolerancia de
# verify_hitrate.sh. Con las fases cortas del piloto daba 1,5 y pasaba, que es
# como se colo hasta aqui.
RATE_ESPERADA = float(os.environ.get("RATE_ESPERADA", "200"))
SEGUNDOS_SANOS = float(os.environ.get("SEGUNDOS_SANOS", "240"))
DERIVA_ADMISIBLE = float(os.environ.get("DERIVA_ADMISIBLE", "0.005"))


def pool_vencido_requerido() -> tuple[int, float]:
    """Tamano minimo del pool vencido y claves que se repoblaran."""
    repobladas = RATE_ESPERADA * (1 - HIT) * STALE_FRACTION * SEGUNDOS_SANOS
    if repobladas <= 0:
        return N_STALE_CFG, 0.0
    minimo = (1 - HIT) * STALE_FRACTION * repobladas / DERIVA_ADMISIBLE
    return int(max(N_STALE_CFG, minimo)), repobladas


N_STALE, REPOBLADAS = pool_vencido_requerido()

TTL = int(os.environ.get("PROFILE_TTL_SECONDS", "900"))
MAX_AGE = int(os.environ.get("PROFILE_MAX_AGE_SECONDS", "86400"))

# Dispersion de la edad del pool CALIENTE. Precargar todas las entradas con
# la misma marca de tiempo hace que "edad del dato servido" -una de las dos
# variables dependientes que cuantifican el trade-off- sea degenerada: mide
# cuanto hace que se corrio la precarga, no la frescura del diseno.
#
# El limite superior no puede acercarse al TTL: una entrada que lo cruce a
# mitad de corrida se convertiria en fallo y la tasa de acierto derivaria,
# que es justo lo que los tres pools existen para evitar. Con TTL de 900 s y
# una corrida de ~380 s (60 de calentamiento + 300 de ventana), 450 s deja
# margen de sobra.
HOT_AGE_SPREAD_S = int(os.environ.get("HOT_AGE_SPREAD_S", "450"))

LOTE = 5000


def _perfil(cid: str, obtenido_en: str) -> bytes:
    # Sin campo `origen`: el origen lo decide COMO se resolvio la peticion,
    # no como se obtuvo el dato. Guardarlo aqui hacia que un acierto de
    # cache se etiquetara como invocacion al proveedor.
    return json.dumps(
        {
            "customer_id": cid,
            "score_pago": 0.95,
            "carga_financiera": 0.30,
            "estabilidad_ingreso": 0.85,
            "antiguedad_meses": 60,
            "obtenido_en": obtenido_en,
        },
        separators=(",", ":"),
    ).encode()


async def _cargar(r, prefijo_id: str, n: int, base, dispersion: int = 0) -> int:
    """Carga n claves con edad `base` mas una dispersion deterministica."""
    pipe = r.pipeline(transaction=False)
    for i in range(n):
        cid = f"{prefijo_id}{i:06d}"
        obtenido_en = base if not dispersion else (
            base - timedelta(seconds=(i * 7919) % dispersion)
        )
        # Sin EX: la edad se evalua en la aplicacion. Si Redis expirara la
        # entrada no quedaria ultimo valor conocido y el brazo C perderia
        # su degradacion elegante.
        pipe.set(f"{PREFIJO}{cid}", _perfil(cid, obtenido_en.isoformat()))
        if (i + 1) % LOTE == 0:
            await pipe.execute()
            pipe = r.pipeline(transaction=False)
    await pipe.execute()
    return n


async def precargar() -> dict:
    r = redis.from_url(REDIS_URL)
    try:
        await r.flushall()
        ahora = datetime.now(timezone.utc)
        # Margen de 120 s por encima del TTL: suficiente para que la entrada
        # cuente como vencida durante toda la ventana de 5 min + calentamiento,
        # y muy por debajo de MAX_AGE para que siga sirviendo de respaldo.
        vencido_en = ahora - timedelta(seconds=TTL + 120)
        assert TTL + 120 < MAX_AGE, "el pool vencido debe seguir siendo utilizable"

        assert HOT_AGE_SPREAD_S < TTL, (
            "la dispersion del pool caliente no puede alcanzar el TTL: las "
            "entradas venceran a mitad de corrida y la tasa de acierto derivara"
        )
        # 7919 es primo y no divide al tamano de los pools, asi que el resto
        # recorre toda la dispersion sin repetir patron: la edad queda
        # repartida de forma uniforme y ademas reproducible entre corridas.
        calientes = await _cargar(r, "cli_h", N_HOT, ahora, HOT_AGE_SPREAD_S)
        vencidas = await _cargar(r, "cli_s", N_STALE, vencido_en)
        info = await r.info("memory")
        stats = await r.info("stats")
        return {
            "calientes": calientes,
            "vencidas": vencidas,
            "vencidas_esperadas_repobladas": int(REPOBLADAS),
            "claves_en_redis": await r.dbsize(),
            "memoria": info.get("used_memory_human"),
            "dispersion_edad_caliente_s": HOT_AGE_SPREAD_S,
            "evicted_keys": int(stats.get("evicted_keys", 0)),
        }
    finally:
        await r.aclose()


async def verificar(res: dict) -> int:
    problemas = []
    if res["evicted_keys"]:
        problemas.append(
            f"Redis evicto {res['evicted_keys']} claves: la tasa de acierto "
            "efectiva NO es la configurada. Subir maxmemory."
        )
    if res["claves_en_redis"] != N_HOT + N_STALE:
        problemas.append(
            f"claves en Redis {res['claves_en_redis']} != esperadas "
            f"{N_HOT + N_STALE}"
        )
    deriva = (1 - HIT) * STALE_FRACTION * REPOBLADAS / N_STALE
    if deriva > 0.02:
        problemas.append(
            f"el pool vencido produce una deriva de {deriva * 100:.2f} puntos "
            "en la tasa de acierto, por encima de la tolerancia de 2 puntos "
            "de verify_hitrate.sh. Subir POOL_STALE."
        )
    for p in problemas:
        print(f"ERROR: {p}", file=sys.stderr)
    return 1 if problemas else 0


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verificar", action="store_true")
    args = ap.parse_args()

    res = await precargar()
    print(
        f"precarga: {res['calientes']} calientes + {res['vencidas']} vencidas "
        f"= {res['claves_en_redis']} claves ({res['memoria']}); "
        "pool frio no acotado (ids aleatorios, cero deriva)"
    )
    deriva = ((1 - HIT) * STALE_FRACTION * REPOBLADAS / N_STALE * 100
              if N_STALE else 0)
    print(
        f"pool vencido: {N_STALE} claves (configurado {N_STALE_CFG}); a "
        f"{RATE_ESPERADA:.0f} sol/s se repoblaran ~{REPOBLADAS:.0f} durante "
        f"los {SEGUNDOS_SANOS:.0f} s sanos -> deriva {deriva:+.2f} puntos"
    )
    print(
        f"objetivo: acierto {HIT:.0%} | de los fallos, "
        f"{STALE_FRACTION:.0%} con valor de respaldo y "
        f"{1 - STALE_FRACTION:.0%} sin el | edad del pool caliente repartida "
        f"en 0-{HOT_AGE_SPREAD_S} s (TTL {TTL} s)"
    )
    return await verificar(res) if args.verificar else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
