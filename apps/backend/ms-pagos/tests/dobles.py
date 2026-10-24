from copy import deepcopy
from decimal import Decimal
from uuid import UUID, uuid4

from app.application.casos_uso import SolicitudCobro
from app.domain.modelos import EventoDominio, Pago
from app.ports.persistencia import ClaveIdempotenciaDuplicada


def solicitud(oferta_id: UUID | None = None, token: str = "tok_visa", monto: str = "250000.00") -> SolicitudCobro:
    return SolicitudCobro(
        solicitud_id=uuid4(),
        oferta_id=oferta_id or uuid4(),
        usuario_id=uuid4(),
        monto=Decimal(monto),
        token_medio_pago=token,
    )


class SuscripcionesFalsas:
    def __init__(self, aceptada: bool = True) -> None:
        self.respuesta = aceptada

    async def aceptada(self, solicitud_id):
        return self.respuesta


class PasarelaEspia:
    """Envuelve una pasarela y cuenta los movimientos que se le piden."""

    def __init__(self, pasarela) -> None:
        self._pasarela = pasarela
        self.movimientos: list[str] = []

    async def cobrar(self, token_medio_pago, monto, idempotency_key):
        self.movimientos.append(idempotency_key)
        return await self._pasarela.cobrar(token_medio_pago, monto, idempotency_key)


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.pagos: dict[UUID, Pago] = {}
        self.tokens: dict[UUID, str] = {}
        self.eventos: list[EventoDominio] = []
        self.chocar_en_proximo_commit: Pago | None = None


class _Pagos:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self):
        return {**self._uow.almacen.pagos, **self._uow.pendientes}

    async def obtener(self, pago_id):
        pago = self._vista().get(pago_id)
        return deepcopy(pago) if pago else None

    async def obtener_por_clave(self, idempotency_key):
        return next((deepcopy(p) for p in self._vista().values() if p.idempotency_key == idempotency_key), None)

    async def agregar(self, pago, token_medio_pago):
        self._uow.pendientes[pago.id] = pago
        self._uow.almacen.tokens[pago.id] = token_medio_pago


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento):
        self._uow.eventos_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, Pago] = {}
        self.eventos_pendientes: list[EventoDominio] = []
        self.pagos = _Pagos(self)
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
            self.almacen.pagos[ganador.id] = ganador
            raise ClaveIdempotenciaDuplicada
        self.almacen.pagos.update(self.pendientes)
        self.almacen.eventos.extend(self.eventos_pendientes)
        self.pendientes.clear()
        self.eventos_pendientes.clear()
