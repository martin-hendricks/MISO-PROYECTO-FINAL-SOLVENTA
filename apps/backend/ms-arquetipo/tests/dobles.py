from copy import deepcopy
from decimal import Decimal
from uuid import UUID

from app.domain.modelos import Ejemplo, EventoDominio
from app.ports.persistencia import ClaveIdempotenciaDuplicada


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.ejemplos: dict[UUID, Ejemplo] = {}
        self.eventos: list[EventoDominio] = []
        self.chocar_en_proximo_commit: Ejemplo | None = None


class _Repo:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, Ejemplo]:
        return {**self._uow.almacen.ejemplos, **self._uow.pendientes}

    async def obtener(self, ejemplo_id):
        e = self._vista().get(ejemplo_id)
        return deepcopy(e) if e else None

    async def obtener_por_clave(self, clave):
        return next((deepcopy(e) for e in self._vista().values() if e.idempotency_key == clave), None)

    async def listar(self, limite):
        return sorted(self._vista().values(), key=lambda e: e.creado_en, reverse=True)[:limite]

    async def indicadores(self):
        todos = self._vista().values()
        return len(todos), sum((e.monto for e in todos), Decimal("0"))

    async def agregar(self, ejemplo):
        self._uow.pendientes[ejemplo.id] = ejemplo

    async def actualizar(self, ejemplo):
        self._uow.pendientes[ejemplo.id] = ejemplo


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento):
        self._uow.eventos_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, Ejemplo] = {}
        self.eventos_pendientes: list[EventoDominio] = []
        self.ejemplos = _Repo(self)
        self.outbox = _Outbox(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.pendientes.clear()
        self.eventos_pendientes.clear()

    async def confirmar(self):
        ganador = self.almacen.chocar_en_proximo_commit
        if ganador is not None:
            self.almacen.chocar_en_proximo_commit = None
            self.almacen.ejemplos[ganador.id] = ganador
            raise ClaveIdempotenciaDuplicada
        self.almacen.ejemplos.update(self.pendientes)
        self.almacen.eventos.extend(self.eventos_pendientes)
        self.pendientes.clear()
        self.eventos_pendientes.clear()
