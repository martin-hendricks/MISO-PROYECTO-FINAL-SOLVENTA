"""Contexto de ejecucion compartido por los brazos.

Concentra lo que los brazos necesitan y no deben construir por su cuenta:
el adaptador, la cache, el motor de tarifa y -sobre todo- el ciclo de vida
de las tareas de refresco en segundo plano.
"""
import asyncio

from . import config
from .adapter import AdaptadorOF
from .cache import CacheOF
from .metrics import REFRESCOS, REFRESCOS_ACTIVOS
from .rating import MotorTarifa


class Contexto:
    def __init__(self, adaptador: AdaptadorOF, cache: CacheOF, rating: MotorTarifa):
        self.adaptador = adaptador
        self.cache = cache
        self.rating = rating
        # Referencias FUERTES a las tareas de refresco. asyncio solo guarda
        # referencias debiles: sin este conjunto el recolector puede llevarse
        # una tarea a medio vuelo, la cache nunca se repoblaria y el brazo C
        # estaria midiendo otra cosa sin que nada lo delate.
        self._tareas: set[asyncio.Task] = set()
        self.en_vuelo: dict[str, asyncio.Task] = {}

    # -- refresco oportunista -----------------------------------------
    def lanzar_refresco(
        self, customer_id: str, clave_coalescencia: str | None = None
    ) -> asyncio.Task | None:
        cota = config.REFRESH_MAX_INFLIGHT
        if cota and len(self._tareas) >= cota:
            REFRESCOS.labels(resultado="rechazado_por_cota").inc()
            return None

        tarea = asyncio.create_task(self._refrescar(customer_id))
        self._tareas.add(tarea)
        REFRESCOS_ACTIVOS.set(len(self._tareas))
        if clave_coalescencia is not None:
            self.en_vuelo[clave_coalescencia] = tarea
        tarea.add_done_callback(
            lambda t: self._al_terminar(t, clave_coalescencia)
        )
        return tarea

    async def _refrescar(self, customer_id: str) -> dict | None:
        """Invoca al proveedor y repuebla la cache.

        La escritura vive aqui y no en el brazo: el refresco puede
        completarse DESPUES de que la respuesta ya salio, y si la escritura
        estuviera en el brazo se perderia.
        """
        try:
            perfil = await self.adaptador.obtener_perfil(customer_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            REFRESCOS.labels(resultado="fallido").inc()
            return None
        if perfil is None:
            REFRESCOS.labels(resultado="fallido").inc()
            return None
        await self.cache.escribir(customer_id, perfil)
        REFRESCOS.labels(resultado="completado").inc()
        return perfil

    def _al_terminar(self, tarea: asyncio.Task, clave: str | None) -> None:
        self._tareas.discard(tarea)
        REFRESCOS_ACTIVOS.set(len(self._tareas))
        if clave is not None and self.en_vuelo.get(clave) is tarea:
            self.en_vuelo.pop(clave, None)
        # Consumir la excepcion: la respuesta ya salio y nadie la espera.
        # Sin esto, cada refresco fallido imprime "Task exception was never
        # retrieved" y el log ahoga la corrida.
        if not tarea.cancelled():
            tarea.exception()

    @property
    def refrescos_activos(self) -> int:
        return len(self._tareas)

    async def drenar(self, timeout: float = 5.0) -> int:
        """Espera a que terminen los refrescos vivos. Devuelve los que quedaron."""
        if self._tareas:
            await asyncio.wait(set(self._tareas), timeout=timeout)
        return len(self._tareas)
