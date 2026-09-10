"""Pruebas de la logica pura del experimento, sin Docker ni red.

Guardan las correcciones descritas en el README (secciones 1, 4 y 5 de
"Desviaciones"): si alguien vuelve a poner el `origen` dentro del blob de
Redis, quita el `shield` o suelta la referencia de la tarea de refresco,
estas pruebas fallan antes de gastar diez horas de corridas.

Uso:  python tests/test_logica.py

Cubre lo que decide la validez de la medicion: las transiciones del
interruptor, la resolucion del perfil en cada brazo y el reparto de origenes.
"""
import asyncio
import os
import pathlib
import sys
import time

RAIZ = os.environ.get(
    "HA01_RAIZ", str(pathlib.Path(__file__).resolve().parent.parent))
sys.path.insert(0, RAIZ)

os.environ.setdefault("DEPENDENCY_BUDGET_MS", "120")
os.environ.setdefault("ADAPTER_HARD_TIMEOUT_MS", "700")
os.environ.setdefault("PROFILE_TTL_SECONDS", "900")
os.environ.setdefault("PROFILE_MAX_AGE_SECONDS", "86400")

from api import strategies as S            # noqa: E402
from api.breaker import Estado, Interruptor  # noqa: E402
from api.cache import edad_segundos        # noqa: E402
from api.metrics import PERFIL_ORIGEN      # noqa: E402

FALLOS = []


def check(nombre, cond, detalle=""):
    marca = "OK  " if cond else "FALLA"
    print(f"  {marca} {nombre}{(' — ' + detalle) if detalle else ''}")
    if not cond:
        FALLOS.append(nombre)


def origenes():
    d = {}
    for m in PERFIL_ORIGEN.collect():
        for s in m.samples:
            if s.name.endswith("_total"):
                d[s.labels["origen"]] = s.value
    return d


# ---------------------------------------------------------------- dobles
class AdaptadorFalso:
    def __init__(self, latencia=0.0, falla=False):
        self.latencia, self.falla = latencia, falla
        self.llamadas = 0

    async def obtener_perfil(self, cid):
        self.llamadas += 1
        await asyncio.sleep(self.latencia)
        if self.falla:
            return None
        return {"customer_id": cid, "score_pago": 0.9, "carga_financiera": 0.2,
                "estabilidad_ingreso": 0.8, "antiguedad_meses": 40,
                "obtenido_en": _ahora()}


class CacheFalsa:
    def __init__(self, datos=None):
        self.datos = dict(datos or {})
        self.escrituras = 0

    async def leer(self, cid):
        return self.datos.get(cid)

    async def escribir(self, cid, perfil):
        self.escrituras += 1
        self.datos[cid] = perfil


class CtxFalso:
    """Replica el contrato de api.context.Contexto sin Redis ni httpx."""

    def __init__(self, adaptador, cache):
        self.adaptador, self.cache = adaptador, cache
        self._tareas, self.en_vuelo = set(), {}

    def lanzar_refresco(self, cid, clave_coalescencia=None):
        t = asyncio.create_task(self._refrescar(cid))
        self._tareas.add(t)
        if clave_coalescencia is not None:
            self.en_vuelo[clave_coalescencia] = t
        t.add_done_callback(lambda x: self._fin(x, clave_coalescencia))
        return t

    async def _refrescar(self, cid):
        p = await self.adaptador.obtener_perfil(cid)
        if p is not None:
            await self.cache.escribir(cid, p)
        return p

    def _fin(self, t, clave):
        self._tareas.discard(t)
        if clave is not None and self.en_vuelo.get(clave) is t:
            self.en_vuelo.pop(clave, None)
        if not t.cancelled():
            t.exception()


def _ahora(delta=0.0):
    from datetime import datetime, timedelta, timezone
    return (datetime.now(timezone.utc) - timedelta(seconds=delta)).isoformat()


# ------------------------------------------------------------ interruptor
def prueba_interruptor():
    print("\n[interruptor]")

    os.environ["BREAKER_POLICY"] = "count"
    os.environ["BREAKER_FAILURE_THRESHOLD"] = "3"
    os.environ["BREAKER_OPEN_SECONDS"] = "0.3"
    os.environ["BREAKER_HALF_OPEN_PROBES"] = "1"
    import importlib
    from api import config
    importlib.reload(config)
    importlib.reload(sys.modules["api.breaker"])
    from api.breaker import Estado as E, Interruptor as I

    b = I()
    for _ in range(2):
        b.registrar(False)
    check("count: no abre antes del umbral", b.estado is E.CERRADO)
    b.registrar(False)
    check("count: abre al alcanzar el umbral", b.estado is E.ABIERTO)
    check("abierto rechaza peticiones", b.permite() is False)

    time.sleep(0.35)
    check("tras el reposo pasa a semiabierto", b.permite() is True
          and b.estado is E.SEMIABIERTO)
    check("semiabierto acota las sondas concurrentes", b.permite() is False,
          "esta es la correccion que evita la estampida de HD-01.8")

    b.registrar(True)
    check("una sonda exitosa cierra", b.estado is E.CERRADO)
    check("al cerrar se vacia la ventana", len(b._muestras) == 0,
          "si no, el primer fallo posterior reabriria de inmediato")
    b.registrar(False)
    check("no reabre con un solo fallo tras cerrar", b.estado is E.CERRADO)

    # politica por tasa
    os.environ["BREAKER_POLICY"] = "rate"
    os.environ["BREAKER_FAILURE_RATE"] = "0.5"
    os.environ["BREAKER_MIN_SAMPLES"] = "5"
    importlib.reload(config)
    importlib.reload(sys.modules["api.breaker"])
    from api.breaker import Estado as E2, Interruptor as I2

    b = I2()
    for _ in range(4):
        b.registrar(False)
    check("rate: no evalua por debajo del minimo de muestras",
          b.estado is E2.CERRADO, "4 fallos con min_samples=5")
    b.registrar(False)
    check("rate: abre al superar la tasa con muestras suficientes",
          b.estado is E2.ABIERTO)


# ---------------------------------------------------------------- brazos
async def prueba_brazos():
    print("\n[brazos]")
    base = origenes()

    def delta(clave):
        return origenes().get(clave, 0) - base.get(clave, 0)

    # A — sin cache, proveedor sano
    ad = AdaptadorFalso()
    r = await S.brazo_directo(CtxFalso(ad, CacheFalsa()), "cli_x")
    check("A sano resuelve por open_finance", r.origen == "open_finance")
    check("A sano no marca degradada", r.degradada is False)

    # A — proveedor caido
    ad = AdaptadorFalso(falla=True)
    r = await S.brazo_directo(CtxFalso(ad, CacheFalsa()), "cli_x")
    check("A caido cae a default", r.origen == "default" and r.degradada)

    # B — acierto de cache
    fresco = {"customer_id": "cli_h1", "score_pago": 0.95,
              "carga_financiera": 0.3, "estabilidad_ingreso": 0.85,
              "antiguedad_meses": 60, "obtenido_en": _ahora(10)}
    ad = AdaptadorFalso()
    ctx = CtxFalso(ad, CacheFalsa({"cli_h1": fresco}))
    r = await S.brazo_cache_bloqueante(ctx, "cli_h1")
    check("B acierto etiqueta origen=cache", r.origen == "cache")
    check("B acierto NO invoca al proveedor", ad.llamadas == 0)
    check("B acierto reporta edad real, no cero", 5 < r.edad_s < 60,
          f"edad={r.edad_s:.1f}s")

    # B — fallo con proveedor caido y valor vencido -> fallback
    vencido = dict(fresco, obtenido_en=_ahora(1000))
    ad = AdaptadorFalso(falla=True)
    ctx = CtxFalso(ad, CacheFalsa({"cli_s1": vencido}))
    r = await S.brazo_cache_bloqueante(ctx, "cli_s1")
    check("B vencido + proveedor caido -> fallback", r.origen == "fallback")
    check("B fallback conserva la edad del dato", r.edad_s > 900,
          f"edad={r.edad_s:.0f}s")

    # C — el proveedor tarda mas que el presupuesto
    ad = AdaptadorFalso(latencia=0.4)
    ctx = CtxFalso(ad, CacheFalsa({"cli_s2": vencido}))
    t0 = time.perf_counter()
    r = await S.brazo_oportunista(ctx, "cli_s2")
    dt = (time.perf_counter() - t0) * 1000
    check("C responde dentro del presupuesto", dt < 200, f"{dt:.0f} ms")
    check("C responde con fallback, no espera al proveedor",
          r.origen == "fallback")

    # ... y la tarea SIGUE VIVA y repuebla la cache (esencia del brazo C)
    await asyncio.sleep(0.5)
    check("C: el refresco continua en segundo plano y escribe en cache",
          ctx.cache.escrituras == 1,
          "sin shield, wait_for cancelaria la tarea y C seria un B")
    check("C: la cache quedo con el dato fresco",
          ctx.cache.datos["cli_s2"]["obtenido_en"] != vencido["obtenido_en"])

    # C — sin valor previo (pool frio) y proveedor caido -> default
    ad = AdaptadorFalso(falla=True)
    ctx = CtxFalso(ad, CacheFalsa())
    r = await S.brazo_oportunista(ctx, "cli_c1")
    check("C frio + proveedor caido -> default", r.origen == "default")

    # C' — coalescencia: N peticiones concurrentes, UNA invocacion
    ad = AdaptadorFalso(latencia=0.3)
    ctx = CtxFalso(ad, CacheFalsa())
    await asyncio.gather(*[
        S.brazo_singleflight(ctx, "cli_c9") for _ in range(20)
    ])
    check("C' coalesce 20 peticiones en 1 invocacion", ad.llamadas == 1,
          f"invocaciones={ad.llamadas}")

    # C sin coalescencia sobre la misma clave: N invocaciones (HD-01.7)
    ad = AdaptadorFalso(latencia=0.3)
    ctx = CtxFalso(ad, CacheFalsa())
    await asyncio.gather(*[
        S.brazo_oportunista(ctx, "cli_c9") for _ in range(20)
    ])
    check("C sin coalescencia produce una invocacion por peticion",
          ad.llamadas == 20, f"invocaciones={ad.llamadas}")

    check("todos los origenes quedaron contabilizados",
          all(delta(o) > 0 for o in ("cache", "open_finance", "fallback", "default")),
          str({o: delta(o) for o in ("cache", "open_finance", "fallback", "default")}))


def prueba_edad():
    print("\n[edad del perfil]")
    check("perfil sin marca de tiempo -> inf",
          edad_segundos({"obtenido_en": None}) == float("inf"))
    check("perfil reciente -> edad pequena",
          edad_segundos({"obtenido_en": _ahora(30)}) > 25)
    check("perfil nulo -> inf", edad_segundos(None) == float("inf"))


def main():
    prueba_interruptor()
    asyncio.run(prueba_brazos())
    prueba_edad()
    print()
    if FALLOS:
        print(f"RESULTADO: {len(FALLOS)} prueba(s) fallaron: {FALLOS}")
        return 1
    print("RESULTADO: todas las pruebas de logica pasaron")
    return 0


if __name__ == "__main__":
    sys.exit(main())
