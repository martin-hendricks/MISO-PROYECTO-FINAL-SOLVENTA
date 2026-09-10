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
N_STALE = int(os.environ.get("POOL_STALE", "100000"))
N_COLD = int(os.environ.get("POOL_COLD", "100000"))
HIT = float(os.environ.get("TARGET_HIT_RATE", "0.96"))
STALE_FRACTION = float(os.environ.get("MISS_STALE_FRACTION", "0.5"))

TTL = int(os.environ.get("PROFILE_TTL_SECONDS", "900"))
MAX_AGE = int(os.environ.get("PROFILE_MAX_AGE_SECONDS", "86400"))

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


async def _cargar(r, prefijo_id: str, n: int, obtenido_en: str) -> int:
    pipe = r.pipeline(transaction=False)
    for i in range(n):
        cid = f"{prefijo_id}{i:06d}"
        # Sin EX: la edad se evalua en la aplicacion. Si Redis expirara la
        # entrada no quedaria ultimo valor conocido y el brazo C perderia
        # su degradacion elegante.
        pipe.set(f"{PREFIJO}{cid}", _perfil(cid, obtenido_en))
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

        calientes = await _cargar(r, "cli_h", N_HOT, ahora.isoformat())
        vencidas = await _cargar(r, "cli_s", N_STALE, vencido_en.isoformat())
        info = await r.info("memory")
        stats = await r.info("stats")
        return {
            "calientes": calientes,
            "vencidas": vencidas,
            "frias_no_precargadas": N_COLD,
            "claves_en_redis": await r.dbsize(),
            "memoria": info.get("used_memory_human"),
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
        f"pool frio de {res['frias_no_precargadas']} ids sin precargar"
    )
    print(
        f"objetivo: acierto {HIT:.0%} | de los fallos, "
        f"{STALE_FRACTION:.0%} con valor de respaldo y "
        f"{1 - STALE_FRACTION:.0%} sin el"
    )
    return await verificar(res) if args.verificar else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
