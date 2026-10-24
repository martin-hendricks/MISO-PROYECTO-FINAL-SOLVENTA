from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, MetaData, Numeric, String, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import Settings
from app.domain.modelos import (
    EstadoSiniestro,
    EvaluacionUmbral,
    EventoDominio,
    EventoParametrico,
    PagoParametrico,
    Siniestro,
    TransicionEstado,
)
from app.ports.persistencia import ClaveIdempotenciaDuplicada

ESQUEMA = "ms_siniestros"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class SiniestroFila(Base):
    __tablename__ = "siniestro"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    evento_id: Mapped[str] = mapped_column(String, unique=True)
    estado: Mapped[str]
    creado_en: Mapped[datetime]


class TransicionEstadoFila(Base):
    __tablename__ = "siniestro_transicion"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    siniestro_id: Mapped[UUID] = mapped_column(ForeignKey(f"{ESQUEMA}.siniestro.id"))
    estado: Mapped[str]
    ocurrido_en: Mapped[datetime]
    origen: Mapped[str]


class EventoParametricoFila(Base):
    __tablename__ = "evento_parametrico"

    evento_id: Mapped[str] = mapped_column(String, primary_key=True)
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    recibido_en: Mapped[datetime]


class EvaluacionUmbralFila(Base):
    __tablename__ = "evaluacion_umbral"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    evento_id: Mapped[str] = mapped_column(String, unique=True)
    umbral: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    valor: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    poliza_vigente: Mapped[bool]
    decision: Mapped[bool]
    motivo: Mapped[str]
    evaluada_en: Mapped[datetime]


class PagoParametricoFila(Base):
    __tablename__ = "pago_parametrico"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    evento_id: Mapped[str] = mapped_column(String, unique=True)
    siniestro_id: Mapped[UUID]
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    pagado_en: Mapped[datetime]


class OutboxFila(Base):
    __tablename__ = "outbox_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str]
    agregado_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    publicado_en: Mapped[datetime | None]


def _siniestro_a_dominio(fila: SiniestroFila, transiciones: list[TransicionEstadoFila]) -> Siniestro:
    historial = [
        TransicionEstado(EstadoSiniestro(t.estado), t.ocurrido_en, t.origen)
        for t in sorted(transiciones, key=lambda t: t.ocurrido_en)
    ]
    return Siniestro(
        id=fila.id,
        evento_id=fila.evento_id,
        estado=EstadoSiniestro(fila.estado),
        historial=historial,
        creado_en=fila.creado_en,
    )


def _evaluacion_a_dominio(fila: EvaluacionUmbralFila) -> EvaluacionUmbral:
    return EvaluacionUmbral(
        id=fila.id,
        evento_id=fila.evento_id,
        umbral=fila.umbral,
        valor=fila.valor,
        poliza_vigente=fila.poliza_vigente,
        decision=fila.decision,
        motivo=fila.motivo,
        evaluada_en=fila.evaluada_en,
    )


def _pago_a_dominio(fila: PagoParametricoFila) -> PagoParametrico:
    return PagoParametrico(
        id=fila.id,
        evento_id=fila.evento_id,
        siniestro_id=fila.siniestro_id,
        monto=fila.monto,
        pagado_en=fila.pagado_en,
    )


def _evento_a_dominio(fila: EventoParametricoFila) -> EventoParametrico:
    return EventoParametrico(evento_id=fila.evento_id, valor=fila.valor, recibido_en=fila.recibido_en)


class RepositorioSiniestrosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener(self, siniestro_id: UUID) -> Siniestro | None:
        fila = await self._s.get(SiniestroFila, siniestro_id)
        if fila is None:
            return None
        transiciones = await self._s.scalars(
            select(TransicionEstadoFila).where(TransicionEstadoFila.siniestro_id == siniestro_id)
        )
        return _siniestro_a_dominio(fila, list(transiciones))

    async def obtener_por_evento(self, evento_id: str) -> Siniestro | None:
        fila = await self._s.scalar(select(SiniestroFila).where(SiniestroFila.evento_id == evento_id))
        if fila is None:
            return None
        return await self.obtener(fila.id)

    async def listar(self, limite: int) -> list[Siniestro]:
        filas = await self._s.scalars(select(SiniestroFila).order_by(SiniestroFila.creado_en.desc()).limit(limite))
        resultado = []
        for fila in filas:
            siniestro = await self.obtener(fila.id)
            if siniestro is not None:
                resultado.append(siniestro)
        return resultado

    async def agregar(self, siniestro: Siniestro) -> None:
        self._s.add(
            SiniestroFila(
                id=siniestro.id,
                evento_id=siniestro.evento_id,
                estado=siniestro.estado.value,
                creado_en=siniestro.creado_en,
            )
        )
        for transicion in siniestro.historial:
            self._s.add(
                TransicionEstadoFila(
                    id=uuid4(),
                    siniestro_id=siniestro.id,
                    estado=transicion.estado.value,
                    ocurrido_en=transicion.ocurrido_en,
                    origen=transicion.origen,
                )
            )
        # Flush inmediato: las filas de transición referencian siniestro_id por FK y deben
        # verse antes de que termine el bloque, igual que el patrón de ms-cotizacion.
        await self._s.flush()

    async def actualizar(self, siniestro: Siniestro) -> None:
        fila = await self._s.get(SiniestroFila, siniestro.id)
        fila.estado = siniestro.estado.value
        ultima = siniestro.historial[-1]
        self._s.add(
            TransicionEstadoFila(
                id=uuid4(),
                siniestro_id=siniestro.id,
                estado=ultima.estado.value,
                ocurrido_en=ultima.ocurrido_en,
                origen=ultima.origen,
            )
        )
        await self._s.flush()


class RepositorioEventosParametricosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_por_clave(self, evento_id: str) -> EventoParametrico | None:
        fila = await self._s.get(EventoParametricoFila, evento_id)
        return _evento_a_dominio(fila) if fila else None

    async def agregar(self, evento: EventoParametrico) -> None:
        self._s.add(
            EventoParametricoFila(evento_id=evento.evento_id, valor=evento.valor, recibido_en=evento.recibido_en)
        )
        await self._s.flush()


class RepositorioEvaluacionesSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_por_evento(self, evento_id: str) -> EvaluacionUmbral | None:
        fila = await self._s.scalar(select(EvaluacionUmbralFila).where(EvaluacionUmbralFila.evento_id == evento_id))
        return _evaluacion_a_dominio(fila) if fila else None

    async def agregar(self, evaluacion: EvaluacionUmbral) -> None:
        self._s.add(
            EvaluacionUmbralFila(
                id=evaluacion.id,
                evento_id=evaluacion.evento_id,
                umbral=evaluacion.umbral,
                valor=evaluacion.valor,
                poliza_vigente=evaluacion.poliza_vigente,
                decision=evaluacion.decision,
                motivo=evaluacion.motivo,
                evaluada_en=evaluacion.evaluada_en,
            )
        )


class RepositorioPagosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_por_evento(self, evento_id: str) -> PagoParametrico | None:
        fila = await self._s.scalar(select(PagoParametricoFila).where(PagoParametricoFila.evento_id == evento_id))
        return _pago_a_dominio(fila) if fila else None

    async def agregar(self, pago: PagoParametrico) -> None:
        self._s.add(
            PagoParametricoFila(
                id=pago.id,
                evento_id=pago.evento_id,
                siniestro_id=pago.siniestro_id,
                monto=pago.monto,
                pagado_en=pago.pagado_en,
            )
        )


class OutboxSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def agregar(self, evento: EventoDominio) -> None:
        self._s.add(
            OutboxFila(id=evento.id, tipo=evento.tipo, agregado_id=evento.agregado_id, payload=evento.payload)
        )


class UnidadDeTrabajoSQL:
    def __init__(self, fabrica: async_sessionmaker[AsyncSession]) -> None:
        self._fabrica = fabrica

    async def __aenter__(self) -> UnidadDeTrabajoSQL:
        self._sesion = self._fabrica()
        self.siniestros = RepositorioSiniestrosSQL(self._sesion)
        self.eventos_parametricos = RepositorioEventosParametricosSQL(self._sesion)
        self.evaluaciones = RepositorioEvaluacionesSQL(self._sesion)
        self.pagos = RepositorioPagosSQL(self._sesion)
        self.outbox = OutboxSQL(self._sesion)
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._sesion.rollback()
        await self._sesion.close()

    async def confirmar(self) -> None:
        try:
            await self._sesion.commit()
        except IntegrityError as exc:
            await self._sesion.rollback()
            mensaje = str(exc.orig)
            if "evento_id" in mensaje or "uq_" in mensaje.lower():
                raise ClaveIdempotenciaDuplicada from exc
            raise


def crear_motor(config: Settings) -> AsyncEngine:
    return create_async_engine(config.database_url, pool_size=config.db_pool_size, pool_pre_ping=True)


def fabrica_unidad_de_trabajo(motor: AsyncEngine):
    sesiones = async_sessionmaker(motor, expire_on_commit=False)
    return lambda: UnidadDeTrabajoSQL(sesiones)
