import time
from collections import deque

from .metrics import CIRCUIT_STATE

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"

_OPEN_DURATION_SECONDS = 5.0
_WINDOW_SECONDS = 10.0
_RATE_THRESHOLD = 0.5  # abre si >= 50% de las llamadas en la ventana fallan
_RATE_MIN_SAMPLES = 10


class CircuitBreaker:
    """Interruptor de circuito con dos políticas de apertura, seleccionables
    por configuración (punto de sensibilidad 4 de HA-01):

    - "count": abre tras N fallos CONSECUTIVOS (umbral simple).
    - "rate": abre cuando la tasa de fallo en una ventana deslizante supera
      un umbral, evitando abrir de forma prematura con tráfico bajo.
    """

    def __init__(self, policy: str, count_threshold: int) -> None:
        self.policy = policy
        self.count_threshold = count_threshold
        self.state = CLOSED
        self._consecutive_failures = 0
        self._opened_at: float | None = None
        self._events: deque[tuple[float, bool]] = deque()  # (ts, success)

    def _prune_window(self, now: float) -> None:
        cutoff = now - _WINDOW_SECONDS
        while self._events and self._events[0][0] < cutoff:
            self._events.popleft()

    def allow_request(self) -> bool:
        now = time.monotonic()
        if self.state == OPEN:
            if self._opened_at is not None and now - self._opened_at >= _OPEN_DURATION_SECONDS:
                self.state = HALF_OPEN
                CIRCUIT_STATE.labels(to_state=HALF_OPEN).inc()
                return True
            return False
        return True

    def record_success(self) -> None:
        now = time.monotonic()
        self._consecutive_failures = 0
        self._events.append((now, True))
        self._prune_window(now)
        if self.state in (OPEN, HALF_OPEN):
            self.state = CLOSED
            CIRCUIT_STATE.labels(to_state=CLOSED).inc()

    def record_failure(self) -> None:
        now = time.monotonic()
        self._consecutive_failures += 1
        self._events.append((now, False))
        self._prune_window(now)

        if self.state == HALF_OPEN:
            self._open(now)
            return

        if self.policy == "count":
            if self._consecutive_failures >= self.count_threshold:
                self._open(now)
        elif self.policy == "rate":
            if len(self._events) >= _RATE_MIN_SAMPLES:
                failures = sum(1 for _, ok in self._events if not ok)
                rate = failures / len(self._events)
                if rate >= _RATE_THRESHOLD:
                    self._open(now)

    def _open(self, now: float) -> None:
        if self.state != OPEN:
            self.state = OPEN
            CIRCUIT_STATE.labels(to_state=OPEN).inc()
        self._opened_at = now
