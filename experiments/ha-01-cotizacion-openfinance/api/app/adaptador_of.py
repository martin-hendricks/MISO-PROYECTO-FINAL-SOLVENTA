import httpx

from .circuit_breaker import CircuitBreaker
from .config import settings
from .metrics import PROVIDER_CALLS, SHED_REQUESTS

# Pool de conexiones dedicado a Open Finance (aislamiento *bulkhead*): las
# llamadas abandonadas por el brazo C/C' no deben agotar los recursos del
# resto del servicio (Anexo A, táctica "Aislamiento de recursos").
_LIMITS = httpx.Limits(max_connections=50, max_keepalive_connections=20)

client: httpx.AsyncClient | None = None
breaker: CircuitBreaker | None = None


async def init_adapter() -> None:
    global client, breaker
    client = httpx.AsyncClient(
        base_url=settings.provider_url,
        limits=_LIMITS,
        timeout=httpx.Timeout(settings.hard_timeout_ms / 1000.0),
    )
    breaker = CircuitBreaker(
        policy=settings.circuit_breaker_policy,
        count_threshold=settings.circuit_breaker_threshold,
    )


async def close_adapter() -> None:
    if client:
        await client.aclose()


async def consultar_perfil(cliente_id: int) -> dict | None:
    """Invoca al proveedor de Open Finance a través del interruptor de
    circuito. Devuelve None si el circuito está abierto, hay timeout o
    error — el llamador decide cómo degradar."""
    assert breaker is not None and client is not None

    if not breaker.allow_request():
        SHED_REQUESTS.inc()
        PROVIDER_CALLS.labels(outcome="circuit_open").inc()
        return None

    try:
        resp = await client.get(f"/perfil/{cliente_id}")
        resp.raise_for_status()
        breaker.record_success()
        PROVIDER_CALLS.labels(outcome="success").inc()
        return resp.json()
    except httpx.TimeoutException:
        breaker.record_failure()
        PROVIDER_CALLS.labels(outcome="timeout").inc()
        return None
    except httpx.HTTPError:
        breaker.record_failure()
        PROVIDER_CALLS.labels(outcome="error").inc()
        return None
