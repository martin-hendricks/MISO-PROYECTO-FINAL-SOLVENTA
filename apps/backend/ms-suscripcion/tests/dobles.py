from copy import deepcopy
from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.modelos import EventoDominio, ReglaSuscripcion, Suscripcion
from app.ports.persistencia import SolicitudYaDecidida


def regla(score_maximo: str = "0.7") -> ReglaSuscripcion:
    return ReglaSuscripcion(
        id=uuid4(),
        score_maximo=Decimal(score_maximo),
        motivo_aceptacion="Riesgo dentro del apetito",
        motivo_rechazo="Riesgo fuera del apetito",
    )


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.suscripciones: dict[UUID, Suscripcion] = {}
        self.eventos: list[EventoDominio] = []
        self.regla: ReglaSuscripcion | None = regla()
        self.chocar_en_proximo_commit: Suscripcion | None = None


class _Suscripciones:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def obtener_por_solicitud(self, solicitud_id):
        vista = {**self._uow.almacen.suscripciones, **self._uow.pendientes}
        return next((deepcopy(s) for s in vista.values() if s.solicitud_id == solicitud_id), None)

    async def agregar(self, suscripcion):
        self._uow.pendientes[suscripcion.id] = suscripcion


class _Reglas:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def vigente(self):
        return self._uow.almacen.regla


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento):
        self._uow.eventos_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, Suscripcion] = {}
        self.eventos_pendientes: list[EventoDominio] = []
        self.suscripciones = _Suscripciones(self)
        self.reglas = _Reglas(self)
        self.outbox = _Outbox(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.pendientes.clear()
        self.eventos_pendientes.clear()

    async def confirmar(self):
        ganadora = self.almacen.chocar_en_proximo_commit
        if ganadora is not None:
            self.almacen.chocar_en_proximo_commit = None
            self.almacen.suscripciones[ganadora.id] = ganadora
            raise SolicitudYaDecidida
        self.almacen.suscripciones.update(self.pendientes)
        self.almacen.eventos.extend(self.eventos_pendientes)
        self.pendientes.clear()
        self.eventos_pendientes.clear()
