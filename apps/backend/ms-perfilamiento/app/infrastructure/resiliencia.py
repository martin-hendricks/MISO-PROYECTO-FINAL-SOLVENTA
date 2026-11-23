from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from prometheus_client import Counter

from app.domain.modelos import CausaDegradacion
from app.ports.adaptadores import PerfilResuelto, consentimiento_en_curso
from app.ports.cache import CacheAtributos, PerfilGuardado

_log = logging.getLogger(__name__)

LECTURAS_CACHE = Counter(
    "perfilamiento_cache_lecturas_total",
    "Lecturas de la cache de perfil por resultado (fresco, vencido o ausente)",
    ["fuente", "resultado"],
)
ERRORES_CACHE = Counter(
    "perfilamiento_cache_errores_total",
    "Operaciones sobre la cache que fallaron o se agotaron; el servicio sigue sin ella",
    ["fuente", "operacion"],
)
LLAMADAS_PROVEEDOR = Counter(
    "perfilamiento_proveedor_llamadas_total",
    "Invocaciones al proveedor por resultado (exito, timeout, error o circuito_abierto)",
    ["fuente", "resultado"],
)
RESPALDOS = Counter(
    "perfilamiento_respaldos_total",
    "Respuestas que no usaron un dato fresco del proveedor (valor vencido o sin valor)",
    ["fuente", "origen"],
)
TRANSICIONES_CIRCUITO = Counter(
    "perfilamiento_circuito_transiciones_total",
    "Cambios de estado del circuit breaker",
    ["fuente", "estado"],
)
COALESCIDAS = Counter(
    "perfilamiento_coalescidas_total",
    "Peticiones que compartieron una invocacion al proveedor ya en vuelo",
    ["fuente"],
)

CERRADO = "cerrado"
ABIERTO = "abierto"
SEMIABIERTO = "semiabierto"


class ProveedorNoDisponible(Exception):
    """El proveedor no se invoco o no devolvio un perfil utilizable."""


class CircuitoAbierto(ProveedorNoDisponible):
    """El circuit breaker esta abierto: la invocacion ni siquiera se intento."""


class InterruptorCircuito:
    """Circuit breaker por tasa de fallo sobre una ventana deslizante. Abre cuando, con al
    menos `min_muestras` llamadas en la ventana, la proporcion de fallos llega al umbral.
    Pasado `apertura_s` deja pasar UNA sola sonda: si sale bien cierra, si falla reabre.
    Un umbral por conteo de fallos consecutivos abriria tarde con trafico bajo."""

    def __init__(
        self,
        fuente: str,
        ventana_s: float = 10.0,
        umbral_tasa: float = 0.5,
        min_muestras: int = 10,
        apertura_s: float = 5.0,
        reloj: Callable[[], float] = time.monotonic,
    ) -> None:
        self.fuente = fuente
        self.estado = CERRADO
        self._ventana_s = ventana_s
        self._umbral_tasa = umbral_tasa
        self._min_muestras = min_muestras
        self._apertura_s = apertura_s
        self._reloj = reloj
        self._eventos: deque[tuple[float, bool]] = deque()
        self._abierto_en = 0.0

    def permitir(self) -> bool:
        if self.estado == ABIERTO and self._reloj() - self._abierto_en >= self._apertura_s:
            self._cambiar(SEMIABIERTO)
            return True
        return self.estado == CERRADO

    def exito(self) -> None:
        if self.estado == SEMIABIERTO:
            self._eventos.clear()
            self._cambiar(CERRADO)
            return
        self._registrar(True)

    def fallo(self) -> None:
        if self.estado == SEMIABIERTO:
            self._abrir()
            return
        self._registrar(False)
        if self.estado != CERRADO or len(self._eventos) < self._min_muestras:
            return
        fallos = sum(1 for _, ok in self._eventos if not ok)
        if fallos / len(self._eventos) >= self._umbral_tasa:
            self._abrir()

    def _registrar(self, ok: bool) -> None:
        ahora = self._reloj()
        self._eventos.append((ahora, ok))
        limite = ahora - self._ventana_s
        while self._eventos and self._eventos[0][0] < limite:
            self._eventos.popleft()

    def _abrir(self) -> None:
        self._abierto_en = self._reloj()
        self._cambiar(ABIERTO)

    def _cambiar(self, estado: str) -> None:
        self.estado = estado
        TRANSICIONES_CIRCUITO.labels(self.fuente, estado).inc()
        _log.warning("circuit breaker de %s: %s", self.fuente, estado)


class AdaptadorResiliente:
    """Decora un adaptador de proveedor con una cache compartida (Redis) y tres protecciones:

    - La cache guarda el valor con su fecha. Pasado `ttl_suave_s` se considera vencido: toca
      refrescarlo, pero NO se descarta; sigue sirviendo de respaldo hasta `ttl_duro_s`.
    - Si no hay un valor fresco se invoca al proveedor con un presupuesto de respuesta
      (`presupuesto_ms`). Si no llega a tiempo se responde con el valor vencido y la
      invocacion sigue en segundo plano, hasta `timeout_proveedor_ms`, para repoblar la cache.
    - El circuit breaker corta las invocaciones mientras el proveedor falle, y las peticiones
      concurrentes por la misma clave comparten una sola invocacion.

    Una cache caida nunca rompe la respuesta: se registra y se consulta al proveedor."""

    def __init__(
        self,
        adaptador: Any,
        cache: CacheAtributos,
        fuente: str,
        *,
        ttl_suave_s: int,
        ttl_duro_s: int,
        presupuesto_ms: int,
        timeout_proveedor_ms: int,
        timeout_cache_ms: int,
        interruptor: InterruptorCircuito,
        ahora: Callable[[], float] = time.time,
    ) -> None:
        self._adaptador = adaptador
        self._cache = cache
        self._fuente = fuente
        self._ttl_suave = ttl_suave_s
        self._ttl_duro = ttl_duro_s
        self._presupuesto = presupuesto_ms / 1000
        self._timeout_proveedor = timeout_proveedor_ms / 1000
        self._timeout_cache = timeout_cache_ms / 1000
        self._interruptor = interruptor
        self._ahora = ahora
        self._en_vuelo: dict[str, asyncio.Task[dict[str, Decimal]]] = {}

    def _clave(self, sujeto: str) -> str:
        return f"perfilamiento:{self._fuente}:{sujeto}"

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        return (await self.obtener_resuelto(cliente_id)).atributos

    async def obtener_resuelto(self, cliente_id: str) -> PerfilResuelto:
        clave = self._clave(cliente_id)
        guardado = await self._leer(clave)
        edad = 0.0 if guardado is None else max(0.0, self._ahora() - guardado.capturado_en)
        if guardado is not None and edad < self._ttl_suave:
            LECTURAS_CACHE.labels(self._fuente, "fresco").inc()
            return PerfilResuelto(guardado.atributos, "cache", edad)
        LECTURAS_CACHE.labels(self._fuente, "ausente" if guardado is None else "vencido").inc()

        try:
            atributos = await asyncio.wait_for(
                asyncio.shield(self._refrescar(cliente_id, clave)), timeout=self._presupuesto
            )
        except Exception as exc:
            if guardado is None:
                RESPALDOS.labels(self._fuente, "sin_valor").inc()
                raise
            RESPALDOS.labels(self._fuente, "cache_vencido").inc()
            _log.warning("%s: se sirve un perfil vencido (%.0f s) por %r", self._fuente, edad, exc)
            causa = CausaDegradacion.TIMEOUT if isinstance(exc, TimeoutError) else CausaDegradacion.FALLO
            return PerfilResuelto(guardado.atributos, "vencido", edad, causa)
        return PerfilResuelto(atributos, "proveedor")

    def _refrescar(self, sujeto: str, clave: str) -> asyncio.Task[dict[str, Decimal]]:
        existente = self._en_vuelo.get(clave)
        if existente is not None and not existente.done():
            COALESCIDAS.labels(self._fuente).inc()
            return existente
        tarea = asyncio.ensure_future(self._invocar_y_guardar(sujeto, clave))
        self._en_vuelo[clave] = tarea
        tarea.add_done_callback(lambda t: self._terminar(clave, t))
        return tarea

    def _terminar(self, clave: str, tarea: asyncio.Task[dict[str, Decimal]]) -> None:
        if self._en_vuelo.get(clave) is tarea:
            del self._en_vuelo[clave]
        if not tarea.cancelled():
            tarea.exception()  # nadie mas la espera si ya se respondio: evita el aviso de excepcion sin recuperar

    async def _invocar_y_guardar(self, sujeto: str, clave: str) -> dict[str, Decimal]:
        if not self._interruptor.permitir():
            LLAMADAS_PROVEEDOR.labels(self._fuente, "circuito_abierto").inc()
            raise CircuitoAbierto(self._fuente)
        try:
            atributos = await asyncio.wait_for(
                self._adaptador.obtener_atributos(sujeto), timeout=self._timeout_proveedor
            )
        except asyncio.CancelledError:
            self._interruptor.fallo()
            raise
        except TimeoutError:
            self._interruptor.fallo()
            LLAMADAS_PROVEEDOR.labels(self._fuente, "timeout").inc()
            raise
        except Exception:
            self._interruptor.fallo()
            LLAMADAS_PROVEEDOR.labels(self._fuente, "error").inc()
            raise
        self._interruptor.exito()
        LLAMADAS_PROVEEDOR.labels(self._fuente, "exito").inc()
        await self._guardar(clave, atributos)
        return atributos

    async def _leer(self, clave: str) -> PerfilGuardado | None:
        try:
            return await asyncio.wait_for(self._cache.leer(clave), timeout=self._timeout_cache)
        except Exception:
            ERRORES_CACHE.labels(self._fuente, "lectura").inc()
            _log.warning("cache %s no disponible al leer; se consulta al proveedor", self._fuente)
            return None

    async def _guardar(self, clave: str, atributos: dict[str, Decimal]) -> None:
        try:
            await asyncio.wait_for(
                self._cache.guardar(clave, atributos, self._ttl_duro, self._ahora(), consentimiento_en_curso.get()),
                timeout=self._timeout_cache,
            )
        except Exception:
            ERRORES_CACHE.labels(self._fuente, "escritura").inc()
            _log.warning("cache %s no disponible al guardar", self._fuente)
