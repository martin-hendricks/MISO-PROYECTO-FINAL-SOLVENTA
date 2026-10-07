from copy import deepcopy
from uuid import UUID

from app.domain.modelos import EventoDominio, SolicitudCotizacion
from app.infrastructure.catalogo_memoria import CatalogoEnMemoria
from app.ports.persistencia import ClaveIdempotenciaDuplicada


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.solicitudes: dict[UUID, SolicitudCotizacion] = {}
        self.eventos: list[EventoDominio] = []
        self.chocar_en_proximo_commit: SolicitudCotizacion | None = None


class _RepoSolicitudes:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, SolicitudCotizacion]:
        return {**self._uow.almacen.solicitudes, **self._uow.pendientes}

    async def obtener(self, solicitud_id):
        s = self._vista().get(solicitud_id)
        return deepcopy(s) if s else None

    async def obtener_por_clave(self, clave):
        return next((deepcopy(s) for s in self._vista().values() if s.idempotency_key == clave), None)

    async def agregar(self, solicitud):
        self._uow.pendientes[solicitud.id] = solicitud

    async def actualizar(self, solicitud):
        self._uow.pendientes[solicitud.id] = solicitud


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento):
        self._uow.eventos_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, SolicitudCotizacion] = {}
        self.eventos_pendientes: list[EventoDominio] = []
        self.solicitudes = _RepoSolicitudes(self)
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
            self.almacen.solicitudes[ganador.id] = ganador
            raise ClaveIdempotenciaDuplicada
        self.almacen.solicitudes.update(self.pendientes)
        self.almacen.eventos.extend(self.eventos_pendientes)
        self.pendientes.clear()
        self.eventos_pendientes.clear()


def catalogo_de_prueba() -> CatalogoEnMemoria:
    return CatalogoEnMemoria()
