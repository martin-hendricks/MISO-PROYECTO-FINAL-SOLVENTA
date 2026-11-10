from copy import deepcopy
from decimal import Decimal
from itertools import count
from uuid import UUID

from app.domain.aviso import Adjunto, Decision, IntentoPago, PagoSiniestro, ParametroRamo
from app.domain.modelos import (
    TipoSiniestro,
    EstadoSiniestro,
    EvaluacionUmbral,
    EventoDominio,
    EventoParametrico,
    PagoParametrico,
    PagoRecibido,
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
        # HU-157: siniestro asistido
        self.adjuntos: list[Adjunto] = []
        self.decisiones: list[Decision] = []
        self.pagos_siniestro: dict[UUID, PagoSiniestro] = {}
        self.intentos_pago: list[IntentoPago] = []
        self.parametros: dict[str, ParametroRamo] = {
            p.ramo: p
            for p in (
                ParametroRamo("proteccion-dispositivo", Decimal("420000"), Decimal("500000")),
                ParametroRamo("vida-crediticia", Decimal("3200000"), Decimal("500000")),
            )
        }
        self.secuencia_numero = count(1001)
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

    async def obtener_por_clave_idempotencia(self, clave):
        return next((deepcopy(s) for s in self._vista().values() if s.clave_idempotencia == clave), None)

    async def listar(self, limite, usuario_id=None):
        filas = self._vista().values()
        if usuario_id is not None:
            filas = [s for s in filas if s.usuario_id == usuario_id]
        return sorted(filas, key=lambda s: s.creado_en, reverse=True)[:limite]

    async def filtrar(self, filtro):
        def pasa(s):
            return (
                (filtro.usuario_id is None or s.usuario_id == filtro.usuario_id)
                and (filtro.tipo is None or s.tipo is filtro.tipo)
                and (filtro.estado is None or s.estado is filtro.estado)
                and (filtro.resultado is None or s.resultado is filtro.resultado)
                and (filtro.requiere_revision is None or s.requiere_revision == filtro.requiere_revision)
            )

        filas = sorted((s for s in self._vista().values() if pasa(s)), key=lambda s: s.creado_en, reverse=True)
        return [deepcopy(s) for s in filas[: filtro.limite]]

    async def contar_avisos_de_poliza_desde(self, poliza_id, desde, excluir):
        return sum(
            1
            for s in self._vista().values()
            if s.poliza_id == poliza_id
            and s.tipo is TipoSiniestro.ASISTIDO
            and s.creado_en >= desde
            and s.id != excluir
        )

    async def tomar_pendientes_de_evaluacion(self, limite):
        filas = sorted(
            (
                s
                for s in self._vista().values()
                if s.tipo is TipoSiniestro.ASISTIDO and s.estado is EstadoSiniestro.RECIBIDO
            ),
            key=lambda s: s.creado_en,
        )
        return [deepcopy(s) for s in filas[:limite]]

    def _pago_recibido(self, siniestro, monto, comprobante, clave, pagado_en):
        poliza = siniestro.poliza
        return PagoRecibido(
            siniestro_id=siniestro.id,
            numero=siniestro.numero,
            tipo=siniestro.tipo,
            ramo=(poliza.ramo or None) if poliza else None,
            poliza_numero=(poliza.numero or None) if poliza else None,
            descripcion=siniestro.descripcion,
            monto=monto,
            comprobante=comprobante,
            clave=clave,
            pagado_en=pagado_en,
        )

    async def _de(self, usuario_id):
        pagos_asistidos = {**self._uow.almacen.pagos_siniestro, **self._uow.pagos_siniestro_pendientes}
        intentos = self._uow.almacen.intentos_pago + self._uow.intentos_pendientes
        parametricos = {**self._uow.almacen.pagos, **self._uow.pagos_pendientes}
        encontrados = []
        for siniestro in self._vista().values():
            if siniestro.usuario_id != usuario_id or siniestro.estado is not EstadoSiniestro.PAGADO:
                continue
            if siniestro.tipo is TipoSiniestro.ASISTIDO:
                pago = pagos_asistidos.get(siniestro.id)
                ejecutado = any(
                    i.siniestro_id == siniestro.id and i.resultado == "ejecutado" for i in intentos
                )
                if pago is None or not ejecutado:
                    continue
                encontrados.append(
                    self._pago_recibido(siniestro, pago.monto, pago.comprobante, pago.clave_idempotencia, pago.pagado_en)
                )
            else:
                pago = next((p for p in parametricos.values() if p.siniestro_id == siniestro.id), None)
                if pago is None:
                    continue
                encontrados.append(
                    self._pago_recibido(siniestro, pago.monto, pago.comprobante, pago.evento_id, pago.pagado_en)
                )
        return sorted(encontrados, key=lambda p: (-p.pagado_en.timestamp(), str(p.siniestro_id)))

    async def listar_pagos_recibidos(self, usuario_id):
        return await self._de(usuario_id)

    async def obtener_pago_recibido(self, siniestro_id, usuario_id):
        return next((p for p in await self._de(usuario_id) if p.siniestro_id == siniestro_id), None)

    async def listar_abiertos_por_poliza(self, poliza_id):
        return [
            deepcopy(s)
            for s in self._vista().values()
            if s.poliza_id == poliza_id and s.estado is not EstadoSiniestro.PAGADO
        ]

    async def agregar(self, siniestro):
        # Igual que el DEFAULT de la base: el número visible lo asigna el almacén.
        siniestro.numero = f"SIN-{next(self._uow.almacen.secuencia_numero)}"
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


class _RepoAdjuntos:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def listar_de(self, siniestro_id):
        todos = self._uow.almacen.adjuntos + self._uow.adjuntos_pendientes
        return [a for a in todos if a.siniestro_id == siniestro_id]

    async def agregar(self, adjunto):
        self._uow.adjuntos_pendientes.append(adjunto)


class _RepoDecisiones:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def listar_de(self, siniestro_id):
        todas = self._uow.almacen.decisiones + self._uow.decisiones_pendientes
        return [d for d in todas if d.siniestro_id == siniestro_id]

    async def agregar(self, decision):
        self._uow.decisiones_pendientes.append(decision)


class _RepoPagosSiniestro:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def obtener_de(self, siniestro_id):
        return {**self._uow.almacen.pagos_siniestro, **self._uow.pagos_siniestro_pendientes}.get(siniestro_id)

    async def agregar(self, pago):
        self._uow.pagos_siniestro_pendientes[pago.siniestro_id] = pago

    async def registrar_intento(self, intento):
        self._uow.intentos_pendientes.append(intento)

    async def listar_intentos(self, siniestro_id):
        todos = self._uow.almacen.intentos_pago + self._uow.intentos_pendientes
        return [i for i in todos if i.siniestro_id == siniestro_id]


class _RepoParametros:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def obtener(self, ramo):
        return self._uow.almacen.parametros.get(ramo)

    async def listar(self):
        return sorted(self._uow.almacen.parametros.values(), key=lambda p: p.ramo)


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
        self.adjuntos_pendientes: list[Adjunto] = []
        self.decisiones_pendientes: list[Decision] = []
        self.pagos_siniestro_pendientes: dict[UUID, PagoSiniestro] = {}
        self.intentos_pendientes: list[IntentoPago] = []
        self.siniestros = _RepoSiniestros(self)
        self.adjuntos = _RepoAdjuntos(self)
        self.decisiones = _RepoDecisiones(self)
        self.pagos_siniestro = _RepoPagosSiniestro(self)
        self.parametros = _RepoParametros(self)
        self.eventos_parametricos = _RepoEventosParametricos(self)
        self.evaluaciones = _RepoEvaluaciones(self)
        self.pagos = _RepoPagos(self)
        self.outbox = _Outbox(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self._limpiar_aviso()
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

        # Choque de idempotencia del pago asistido (UNIQUE siniestro_id en pago_siniestro).
        for siniestro_id in self.pagos_siniestro_pendientes:
            if siniestro_id in self.almacen.pagos_siniestro:
                raise ClaveIdempotenciaDuplicada
        # Choque de idempotencia del aviso (UNIQUE clave_idempotencia en siniestro).
        claves = {s.clave_idempotencia for s in self.almacen.siniestros.values() if s.clave_idempotencia}
        for sid, pendiente in self.siniestros_pendientes.items():
            if sid not in self.almacen.siniestros and pendiente.clave_idempotencia in claves:
                raise ClaveIdempotenciaDuplicada

        self.almacen.siniestros.update(self.siniestros_pendientes)
        self.almacen.eventos_parametricos.update(self.eventos_pendientes)
        self.almacen.evaluaciones.update(self.evaluaciones_pendientes)
        self.almacen.pagos.update(self.pagos_pendientes)
        self.almacen.eventos.extend(self.eventos_dominio_pendientes)
        self.almacen.adjuntos.extend(self.adjuntos_pendientes)
        self.almacen.decisiones.extend(self.decisiones_pendientes)
        self.almacen.pagos_siniestro.update(self.pagos_siniestro_pendientes)
        self.almacen.intentos_pago.extend(self.intentos_pendientes)
        self._limpiar_aviso()

        self.siniestros_pendientes.clear()
        self.eventos_pendientes.clear()
        self.evaluaciones_pendientes.clear()
        self.pagos_pendientes.clear()
        self.eventos_dominio_pendientes.clear()

    def _limpiar_aviso(self):
        self.adjuntos_pendientes.clear()
        self.decisiones_pendientes.clear()
        self.pagos_siniestro_pendientes.clear()
        self.intentos_pendientes.clear()
