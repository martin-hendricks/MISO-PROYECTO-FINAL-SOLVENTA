"""`:AdaptadorOF` — capa anticorrupcion sobre el proveedor de Open Finance.

Aloja el timeout duro (EC-LAT-08), el interruptor y el pool dedicado por
proveedor (bulkhead).

NO conoce DEPENDENCY_BUDGET_MS. Es deliberado y es la esencia de la
hipotesis: los dos timeouts pertenecen a componentes distintos. Si el
adaptador conociera el presupuesto de la cotizacion no habria dos relojes
sino uno, y el experimento no probaria nada.
"""
from datetime import datetime, timezone

import httpx

from . import config
from .breaker import Interruptor
from .metrics import (
    ADAPTER_CALLS,
    ADAPTER_INFLIGHT,
    ADAPTER_LAT,
    LLAMADAS_FALLIDAS,
)

RUTA = "/open-finance/v1/customers/{cid}/financial-data"


class AdaptadorOF:
    def __init__(self) -> None:
        self._cliente = httpx.AsyncClient(
            base_url=config.PROVIDER_BASE_URL,
            timeout=httpx.Timeout(
                config.ADAPTER_HARD_TIMEOUT_S,
                connect=config.ADAPTER_CONNECT_TIMEOUT_S,
            ),
            limits=httpx.Limits(
                max_connections=config.ADAPTER_MAX_CONNECTIONS,
                max_keepalive_connections=config.ADAPTER_MAX_KEEPALIVE,
            ),
            # Sin reintentos: un reintento silencioso duplicaria la carga
            # sobre el proveedor justo cuando esta degradado y descuadraria
            # ha01_provider_requests_total contra ha01_adapter_calls_total.
            transport=httpx.AsyncHTTPTransport(retries=0),
        )
        self.interruptor = Interruptor()

    async def aclose(self) -> None:
        await self._cliente.aclose()

    async def obtener_perfil(self, customer_id: str) -> dict | None:
        if not self.interruptor.permite():
            ADAPTER_CALLS.labels(resultado="cortada_por_breaker").inc()
            return None

        ADAPTER_INFLIGHT.inc()
        try:
            with ADAPTER_LAT.time():
                r = await self._cliente.get(RUTA.format(cid=customer_id))

            if r.status_code >= 500:
                self.interruptor.registrar(False)
                ADAPTER_CALLS.labels(resultado="error_5xx").inc()
                LLAMADAS_FALLIDAS.inc()
                return None
            if r.status_code >= 400:
                # Error de negocio (429 por cuota, 4xx de contrato). No
                # cuenta como falla de disponibilidad: abrir el interruptor
                # por un 429 castigaria al proveedor por nuestra propia
                # tasa de llamada.
                ADAPTER_CALLS.labels(resultado=f"error_{r.status_code}").inc()
                return None

            self.interruptor.registrar(True)
            ADAPTER_CALLS.labels(resultado="ok").inc()
            return self._a_canonico(customer_id, r.json())

        except (httpx.TimeoutException, httpx.TransportError):
            self.interruptor.registrar(False)
            ADAPTER_CALLS.labels(resultado="falla_transporte").inc()
            LLAMADAS_FALLIDAS.inc()
            return None
        finally:
            ADAPTER_INFLIGHT.dec()

    @staticmethod
    def _a_canonico(customer_id: str, crudo: dict) -> dict:
        pb = crudo["payment_behavior"]
        ing = crudo["income"]
        obl = crudo["obligations"][0] if crudo["obligations"] else {"utilization": 0.0}
        return {
            "customer_id": customer_id,
            "score_pago": pb["on_time_ratio_12m"],
            "carga_financiera": obl["utilization"],
            "estabilidad_ingreso": ing["stability_index"],
            "antiguedad_meses": ing["months_observed"],
            "obtenido_en": datetime.now(timezone.utc).isoformat(),
        }
