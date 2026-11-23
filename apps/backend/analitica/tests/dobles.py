from collections import Counter
from datetime import date

from app.ports.persistencia import EventoYaProcesado


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.conteos: Counter[tuple[str, date]] = Counter()
        self.eventos_procesados: set[str] = set()


class _Metricas:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def incrementar(self, evento_id_str: str, tipo: str, fecha: date) -> bool:
        if evento_id_str in self._uow.almacen.eventos_procesados or evento_id_str in self._uow.pendientes_eventos:
            raise EventoYaProcesado
        self._uow.pendientes_eventos.add(evento_id_str)
        self._uow.pendientes_conteos[(tipo, fecha)] += 1
        return True

    async def listar(self, desde: date, hasta: date):
        from app.domain.modelos import ConteoEventos

        return sorted(
            (
                ConteoEventos(tipo=tipo, fecha=fecha, cantidad=cantidad)
                for (tipo, fecha), cantidad in self._uow.almacen.conteos.items()
                if desde <= fecha <= hasta
            ),
            key=lambda c: (c.fecha, c.tipo),
        )


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes_eventos: set[str] = set()
        self.pendientes_conteos: Counter[tuple[str, date]] = Counter()
        self.metricas = _Metricas(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.pendientes_eventos.clear()
        self.pendientes_conteos.clear()

    async def confirmar(self):
        self.almacen.eventos_procesados.update(self.pendientes_eventos)
        self.almacen.conteos.update(self.pendientes_conteos)
        self.pendientes_eventos.clear()
        self.pendientes_conteos.clear()
