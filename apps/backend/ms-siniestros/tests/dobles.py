from copy import deepcopy
from uuid import UUID

from app.domain.modelos import (
    EvaluacionUmbral,
    EventoDominio,
    EventoParametrico,
    PagoParametrico,
    Siniestro,
)
from app.ports.persistencia import ClaveIdempotenciaDuplicada


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.siniestros: dict[UUID, Siniestro] = {}
        self.eventos_parametricos: dict[str, EventoParametrico] = {}
        self.evaluaciones: dict[str, EvaluacionUmbral] = {}
        self.pagos: dict[str, PagoParametrico] = {}
        self.eventos: list[EventoDominio] = []
        self.chocar_evento_en_proximo_commit: str | None = None
        self.chocar_pago_en_proximo_commit: str | None = None


class _RepoSiniestros:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, Siniestro]:
        return {**self._uow.almacen.siniestros, **self._uow.siniestros_pendientes}

    async def obtener(self, siniestro_id):
        s = self._vista().get(siniestro_id)
        return deepcopy(s) if s else None

    async def obtener_por_evento(self, evento_id):
        return next((deepcopy(s) for s in self._vista().values() if s.evento_id == evento_id), None)

    async def listar(self, limite):
        return sorted(self._vista().values(), key=lambda s: s.creado_en, reverse=True)[:limite]

    async def agregar(self, siniestro):
        self._uow.siniestros_pendientes[siniestro.id] = deepcopy(siniestro)

    async def actualizar(self, siniestro):
        self._uow.siniestros_pendientes[siniestro.id] = deepcopy(siniestro)


class _RepoEventosParametricos:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[str, EventoParametrico]:
        return {**self._uow.almacen.eventos_parametricos, **self._uow.eventos_pendientes}

    async def obtener_por_clave(self, evento_id):
        e = self._vista().get(evento_id)
        return deepcopy(e) if e else None

    async def agregar(self, evento):
        self._uow.eventos_pendientes[evento.evento_id] = deepcopy(evento)


class _RepoEvaluaciones:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[str, EvaluacionUmbral]:
        return {**self._uow.almacen.evaluaciones, **self._uow.evaluaciones_pendientes}

    async def obtener_por_evento(self, evento_id):
        e = self._vista().get(evento_id)
        return deepcopy(e) if e else None

    async def agregar(self, evaluacion):
        self._uow.evaluaciones_pendientes[evaluacion.evento_id] = deepcopy(evaluacion)


class _RepoPagos:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[str, PagoParametrico]:
        return {**self._uow.almacen.pagos, **self._uow.pagos_pendientes}

    async def obtener_por_evento(self, evento_id):
        p = self._vista().get(evento_id)
        return deepcopy(p) if p else None

    async def agregar(self, pago):
        self._uow.pagos_pendientes[pago.evento_id] = deepcopy(pago)


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento):
        self._uow.eventos_dominio_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    """Doble en memoria del Protocol UnidadDeTrabajo, igual patrón que ms-arquetipo:
    permite probar el núcleo (dominio + casos de uso) sin PostgreSQL ni red, incluyendo
    la simulación de choque de idempotencia en el commit."""

    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.siniestros_pendientes: dict[UUID, Siniestro] = {}
        self.eventos_pendientes: dict[str, EventoParametrico] = {}
        self.evaluaciones_pendientes: dict[str, EvaluacionUmbral] = {}
        self.pagos_pendientes: dict[str, PagoParametrico] = {}
        self.eventos_dominio_pendientes: list[EventoDominio] = []
        self.siniestros = _RepoSiniestros(self)
        self.eventos_parametricos = _RepoEventosParametricos(self)
        self.evaluaciones = _RepoEvaluaciones(self)
        self.pagos = _RepoPagos(self)
        self.outbox = _Outbox(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.siniestros_pendientes.clear()
        self.eventos_pendientes.clear()
        self.evaluaciones_pendientes.clear()
        self.pagos_pendientes.clear()
        self.eventos_dominio_pendientes.clear()

    async def confirmar(self):
        forzar_choque_evento = self.almacen.chocar_evento_en_proximo_commit
        if forzar_choque_evento is not None and forzar_choque_evento in self.eventos_pendientes:
            self.almacen.chocar_evento_en_proximo_commit = None
            raise ClaveIdempotenciaDuplicada

        forzar_choque_pago = self.almacen.chocar_pago_en_proximo_commit
        if forzar_choque_pago is not None and forzar_choque_pago in self.pagos_pendientes:
            self.almacen.chocar_pago_en_proximo_commit = None
            raise ClaveIdempotenciaDuplicada

        # Choque real: dos agregados pendientes con la misma clave natural ya existente.
        for evento_id in self.eventos_pendientes:
            if evento_id in self.almacen.eventos_parametricos:
                raise ClaveIdempotenciaDuplicada
        for evento_id in self.pagos_pendientes:
            if evento_id in self.almacen.pagos:
                raise ClaveIdempotenciaDuplicada

        self.almacen.siniestros.update(self.siniestros_pendientes)
        self.almacen.eventos_parametricos.update(self.eventos_pendientes)
        self.almacen.evaluaciones.update(self.evaluaciones_pendientes)
        self.almacen.pagos.update(self.pagos_pendientes)
        self.almacen.eventos.extend(self.eventos_dominio_pendientes)

        self.siniestros_pendientes.clear()
        self.eventos_pendientes.clear()
        self.evaluaciones_pendientes.clear()
        self.pagos_pendientes.clear()
        self.eventos_dominio_pendientes.clear()
