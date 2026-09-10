"""Interruptor de circuito con las dos politicas de apertura.

Se implementa aqui y no con libreria porque el punto de sensibilidad 4
exige comparar ambas politicas (conteo de fallos consecutivos contra tasa
sobre ventana deslizante) e instrumentar cada transicion de estado.
"""
import time
from collections import deque
from enum import Enum

from . import config
from .metrics import BREAKER_ABIERTO_SEGUNDOS, BREAKER_STATE, BREAKER_TRANSITIONS

_NIVEL = {"cerrado": 0, "semiabierto": 1, "abierto": 2}


class Estado(str, Enum):
    CERRADO = "cerrado"
    ABIERTO = "abierto"
    SEMIABIERTO = "semiabierto"


class Interruptor:
    def __init__(self) -> None:
        self.politica = config.BREAKER_POLICY
        self.umbral_conteo = config.BREAKER_FAILURE_THRESHOLD
        self.umbral_tasa = config.BREAKER_FAILURE_RATE
        self.ventana = config.BREAKER_WINDOW_SECONDS
        self.min_muestras = config.BREAKER_MIN_SAMPLES
        self.reposo = config.BREAKER_OPEN_SECONDS
        self.max_sondas = max(1, config.BREAKER_HALF_OPEN_PROBES)

        self.estado = Estado.CERRADO
        self._fallos_seguidos = 0
        self._muestras: deque = deque()      # (monotonic, exito: bool)
        self._abierto_desde = 0.0
        self._sondas_en_vuelo = 0
        BREAKER_STATE.set(0)
        BREAKER_ABIERTO_SEGUNDOS.set(0)

    # -- decision de admision -----------------------------------------
    def permite(self) -> bool:
        if self.estado is Estado.ABIERTO:
            if time.monotonic() - self._abierto_desde < self.reposo:
                return False
            self._transicion(Estado.SEMIABIERTO)
            self._sondas_en_vuelo = 1
            return True

        if self.estado is Estado.SEMIABIERTO:
            # Sin esta cota, TODAS las peticiones pasarian mientras el
            # estado sea semiabierto: cientos de sondas simultaneas contra
            # un proveedor que apenas se recupera. Es exactamente la
            # estampida que HD-01.8 dice que no debe ocurrir.
            if self._sondas_en_vuelo >= self.max_sondas:
                return False
            self._sondas_en_vuelo += 1
            return True

        return True

    # -- realimentacion -----------------------------------------------
    def registrar(self, exito: bool) -> None:
        ahora = time.monotonic()
        self._muestras.append((ahora, exito))
        self._podar(ahora)

        if self.estado is Estado.SEMIABIERTO:
            self._sondas_en_vuelo = max(0, self._sondas_en_vuelo - 1)

        if exito:
            self._fallos_seguidos = 0
            if self.estado is Estado.SEMIABIERTO:
                self._cerrar()
            return

        self._fallos_seguidos += 1
        if self.estado is Estado.SEMIABIERTO or self._debe_abrir():
            self._abrir()

    def _podar(self, ahora: float) -> None:
        while self._muestras and ahora - self._muestras[0][0] > self.ventana:
            self._muestras.popleft()

    def _debe_abrir(self) -> bool:
        if self.politica == "count":
            return self._fallos_seguidos >= self.umbral_conteo
        # Politica `rate`: proporcion de fallos sobre ventana deslizante.
        # El minimo de muestras evita abrir por un solo fallo con trafico
        # bajo; la ventana temporal evita el problema inverso de `count`,
        # que con trafico bajo nunca acumula N fallos consecutivos antes
        # de que el ASR se rompa. Esa es la comparacion de HD-01.6.
        if len(self._muestras) < self.min_muestras:
            return False
        fallos = sum(1 for _, ok in self._muestras if not ok)
        return fallos / len(self._muestras) >= self.umbral_tasa

    def _abrir(self) -> None:
        self._abierto_desde = time.monotonic()
        self._sondas_en_vuelo = 0
        BREAKER_ABIERTO_SEGUNDOS.set(time.time())
        self._transicion(Estado.ABIERTO)

    def _cerrar(self) -> None:
        # Vaciar la ventana es indispensable: si se conservara, los fallos
        # previos seguirian dentro y el primer fallo posterior reabriria de
        # inmediato. El interruptor oscilaria durante la fase de
        # recuperacion y el "tiempo hasta cerrar" de HD-01.8 saldria mal.
        self._muestras.clear()
        self._fallos_seguidos = 0
        self._sondas_en_vuelo = 0
        BREAKER_ABIERTO_SEGUNDOS.set(0)
        self._transicion(Estado.CERRADO)

    def _transicion(self, nuevo: Estado) -> None:
        if nuevo is self.estado:
            return
        BREAKER_TRANSITIONS.labels(desde=self.estado.value, hacia=nuevo.value).inc()
        self.estado = nuevo
        BREAKER_STATE.set(_NIVEL[nuevo.value])

    # -- introspeccion para /info y las verificaciones de sanidad ------
    def snapshot(self) -> dict:
        return {
            "estado": self.estado.value,
            "politica": self.politica,
            "fallos_seguidos": self._fallos_seguidos,
            "muestras_en_ventana": len(self._muestras),
            "sondas_en_vuelo": self._sondas_en_vuelo,
        }
