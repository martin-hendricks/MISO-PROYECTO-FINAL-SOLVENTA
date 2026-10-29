from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, DateTime, MetaData, Numeric, String, func, select
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
from app.domain.modelos import Decision, EventoDominio, ReglaSuscripcion, Suscripcion
from app.ports.persistencia import SolicitudYaDecidida

ESQUEMA = "ms_suscripcion"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class SuscripcionFila(Base):
    __tablename__ = "suscripcion"

    suscripcion_id: Mapped[UUID] = mapped_column(primary_key=True)
    solicitud_id: Mapped[UUID] = mapped_column(unique=True)
    perfil_id: Mapped[UUID]
    decision: Mapped[str]
    motivo: Mapped[str | None] = mapped_column(String)
    regla: Mapped[str | None] = mapped_column(String)
    evaluada_en: Mapped[datetime]


class ReglaFila(Base):
    __tablename__ = "regla_suscripcion"

    regla_id: Mapped[UUID] = mapped_column(primary_key=True)
    score_maximo: Mapped[Decimal] = mapped_column(Numeric(10, 4))
    motivo_aceptacion: Mapped[str]
    motivo_rechazo: Mapped[str]
    vigente: Mapped[bool]


class OutboxFila(Base):
    __tablename__ = "outbox_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str]
    agregado_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    publicado_en: Mapped[datetime | None]


def _a_dominio(fila: SuscripcionFila) -> Suscripcion:
    return Suscripcion(
        id=fila.suscripcion_id,
        solicitud_id=fila.solicitud_id,
        perfil_id=fila.perfil_id,
        decision=Decision(fila.decision),
        motivo=fila.motivo or "",
        evaluada_en=fila.evaluada_en,
        regla=fila.regla or "",
    )


class RepositorioSuscripcionesSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_por_solicitud(self, solicitud_id: UUID) -> Suscripcion | None:
        fila = await self._s.scalar(select(SuscripcionFila).where(SuscripcionFila.solicitud_id == solicitud_id))
        return _a_dominio(fila) if fila else None

    async def agregar(self, suscripcion: Suscripcion) -> None:
        self._s.add(
            SuscripcionFila(
                suscripcion_id=suscripcion.id,
                solicitud_id=suscripcion.solicitud_id,
                perfil_id=suscripcion.perfil_id,
                decision=suscripcion.decision.value,
                motivo=suscripcion.motivo,
                regla=suscripcion.regla,
                evaluada_en=suscripcion.evaluada_en,
            )
        )


class RepositorioReglasSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def vigente(self) -> ReglaSuscripcion | None:
        fila = await self._s.scalar(select(ReglaFila).where(ReglaFila.vigente.is_(True)))
        if fila is None:
            return None
        return ReglaSuscripcion(
            id=fila.regla_id,
            score_maximo=fila.score_maximo,
            motivo_aceptacion=fila.motivo_aceptacion,
            motivo_rechazo=fila.motivo_rechazo,
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
        self.suscripciones = RepositorioSuscripcionesSQL(self._sesion)
        self.reglas = RepositorioReglasSQL(self._sesion)
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
            if "uq_suscripcion_solicitud" in str(exc.orig):
                raise SolicitudYaDecidida from exc
            raise


def crear_motor(config: Settings) -> AsyncEngine:
    return create_async_engine(config.database_url, pool_size=config.db_pool_size, pool_pre_ping=True)


def fabrica_unidad_de_trabajo(motor: AsyncEngine):
    sesiones = async_sessionmaker(motor, expire_on_commit=False)
    return lambda: UnidadDeTrabajoSQL(sesiones)
