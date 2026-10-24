from copy import deepcopy
from decimal import Decimal
from uuid import UUID, uuid4

from app.application.casos_uso import SolicitudEmision
from app.domain.modelos import Cobertura, EventoDominio, Poliza
from app.ports.persistencia import PolizaYaEmitida


def coberturas() -> list[Cobertura]:
    return [
        Cobertura(nombre="Responsabilidad civil", suma_asegurada=Decimal("50000000.00"), deducible=Decimal("0")),
        Cobertura(nombre="Daños totales", suma_asegurada=Decimal("80000000.00"), deducible=Decimal("1000000.00")),
    ]


def solicitud(oferta_id: UUID | None = None) -> SolicitudEmision:
    return SolicitudEmision(
        solicitud_id=uuid4(),
        oferta_id=oferta_id or uuid4(),
        usuario_id=uuid4(),
        token_pago_confirmado=uuid4(),
        coberturas=coberturas(),
    )


class SuscripcionesFalsas:
    def __init__(self, aceptada: bool = True) -> None:
        self.respuesta = aceptada
        self.consultas: list[UUID] = []

    async def aceptada(self, solicitud_id):
        self.consultas.append(solicitud_id)
        return self.respuesta


class CobrosFalsos:
    def __init__(self, exitoso: bool = True) -> None:
        self.respuesta = exitoso

    async def exitoso(self, oferta_id, token_pago_confirmado):
        return self.respuesta


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.polizas: dict[UUID, Poliza] = {}
        self.eventos: list[EventoDominio] = []
        self.secuencia = 0
        self.chocar_en_proximo_commit: Poliza | None = None


class _Polizas:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self):
        return {**self._uow.almacen.polizas, **self._uow.pendientes}

    async def obtener(self, poliza_id):
        poliza = self._vista().get(poliza_id)
        return deepcopy(poliza) if poliza else None

    async def obtener_por_oferta(self, oferta_id):
        return next((deepcopy(p) for p in self._vista().values() if p.oferta_id == oferta_id), None)

    async def obtener_por_numero(self, numero):
        return next((deepcopy(p) for p in self._vista().values() if p.numero == numero), None)

    async def listar_por_usuario(self, usuario_id, limite):
        polizas = sorted(
            (p for p in self._vista().values() if p.usuario_id == usuario_id),
            key=lambda p: p.inicio_vigencia,
            reverse=True,
        )
        return [deepcopy(p) for p in polizas[:limite]]

    async def siguiente_secuencia(self):
        # Como una secuencia de PostgreSQL: avanza aunque la transacción se revierta.
        self._uow.almacen.secuencia += 1
        return self._uow.almacen.secuencia

    async def agregar(self, poliza):
        self._uow.pendientes[poliza.id] = poliza


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento):
        self._uow.eventos_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, Poliza] = {}
        self.eventos_pendientes: list[EventoDominio] = []
        self.polizas = _Polizas(self)
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
            self.almacen.polizas[ganadora.id] = ganadora
            raise PolizaYaEmitida
        self.almacen.polizas.update(self.pendientes)
        self.almacen.eventos.extend(self.eventos_pendientes)
        self.pendientes.clear()
        self.eventos_pendientes.clear()
