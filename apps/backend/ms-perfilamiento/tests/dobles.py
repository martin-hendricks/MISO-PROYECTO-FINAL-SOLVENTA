from __future__ import annotations

import asyncio
from copy import deepcopy
from decimal import Decimal
from uuid import UUID

from app.domain.modelos import Consentimiento, EventoDominio, Oferta
from app.ports.persistencia import ClaveIdempotenciaDuplicada


class AdaptadorConfigurable:
    """Doble de test (HU-56) para AdaptadorOpenFinance/AdaptadorOpenData: permite forzar
    en los tests una respuesta que nunca llega (`lento=True`) o fallida (`fallar=True`)
    sin depender de red real ni de dormir tiempo real (los tests unitarios de CI no
    permiten pausas fijas). `lento=True` espera un `asyncio.Event` que nunca se
    dispara, así que es el timeout real de `asyncio.wait_for` en el caso de uso -- no
    una espera fija de este doble -- el que corta la llamada, ejerciendo el camino de
    `asyncio.wait_for` expirando y la captura de excepción."""

    def __init__(self, atributos: dict[str, Decimal], lento: bool = False, fallar: bool = False) -> None:
        self._atributos = atributos
        self._lento = lento
        self._fallar = fallar

    async def obtener_atributos(self, cliente_id: str) -> dict[str, Decimal]:
        if self._lento:
            await asyncio.Event().wait()
        if self._fallar:
            raise RuntimeError("doble de adaptador: fallo simulado")
        return dict(self._atributos)


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.consentimientos: dict[UUID, Consentimiento] = {}
        self.ofertas: dict[UUID, Oferta] = {}
        self.ofertas_por_clave: dict[str, UUID] = {}
        self.eventos: list[EventoDominio] = []
        self.chocar_en_proximo_commit: tuple[str, Oferta] | None = None


class _RepoConsentimientos:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, Consentimiento]:
        return {**self._uow.almacen.consentimientos, **self._uow.consentimientos_pendientes}

    async def obtener_vigente(self, cliente_id: str) -> Consentimiento | None:
        candidatos = [c for c in self._vista().values() if c.cliente_id == cliente_id and c.vigente]
        if not candidatos:
            return None
        return deepcopy(max(candidatos, key=lambda c: c.otorgado_en))

    async def obtener_por_id(self, consentimiento_id: UUID) -> Consentimiento | None:
        c = self._vista().get(consentimiento_id)
        return deepcopy(c) if c else None

    async def agregar(self, consentimiento: Consentimiento) -> None:
        self._uow.consentimientos_pendientes[consentimiento.id] = consentimiento

    async def actualizar(self, consentimiento: Consentimiento) -> None:
        self._uow.consentimientos_pendientes[consentimiento.id] = consentimiento


class _RepoOfertas:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, Oferta]:
        return {**self._uow.almacen.ofertas, **self._uow.ofertas_pendientes}

    def _vista_claves(self) -> dict[str, UUID]:
        return {**self._uow.almacen.ofertas_por_clave, **self._uow.claves_pendientes}

    async def obtener(self, oferta_id: UUID) -> Oferta | None:
        o = self._vista().get(oferta_id)
        return deepcopy(o) if o else None

    async def obtener_por_clave(self, idempotency_key: str) -> Oferta | None:
        oferta_id = self._vista_claves().get(idempotency_key)
        if oferta_id is None:
            return None
        return deepcopy(self._vista().get(oferta_id))

    async def agregar(self, idempotency_key: str, oferta: Oferta) -> None:
        self._uow.ofertas_pendientes[oferta.id] = oferta
        self._uow.claves_pendientes[idempotency_key] = oferta.id


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento: EventoDominio) -> None:
        self._uow.eventos_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.consentimientos_pendientes: dict[UUID, Consentimiento] = {}
        self.ofertas_pendientes: dict[UUID, Oferta] = {}
        self.claves_pendientes: dict[str, UUID] = {}
        self.eventos_pendientes: list[EventoDominio] = []
        self.consentimientos = _RepoConsentimientos(self)
        self.ofertas = _RepoOfertas(self)
        self.outbox = _Outbox(self)

    async def __aenter__(self) -> "UnidadDeTrabajoEnMemoria":
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.consentimientos_pendientes.clear()
        self.ofertas_pendientes.clear()
        self.claves_pendientes.clear()
        self.eventos_pendientes.clear()

    async def confirmar(self) -> None:
        choque = self.almacen.chocar_en_proximo_commit
        if choque is not None:
            self.almacen.chocar_en_proximo_commit = None
            clave_ganadora, oferta_ganadora = choque
            self.almacen.ofertas[oferta_ganadora.id] = oferta_ganadora
            self.almacen.ofertas_por_clave[clave_ganadora] = oferta_ganadora.id
            raise ClaveIdempotenciaDuplicada
        self.almacen.consentimientos.update(self.consentimientos_pendientes)
        self.almacen.ofertas.update(self.ofertas_pendientes)
        self.almacen.ofertas_por_clave.update(self.claves_pendientes)
        self.almacen.eventos.extend(self.eventos_pendientes)
        self.consentimientos_pendientes.clear()
        self.ofertas_pendientes.clear()
        self.claves_pendientes.clear()
        self.eventos_pendientes.clear()
