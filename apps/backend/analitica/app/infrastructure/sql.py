from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, Integer, MetaData, String, UniqueConstraint, select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import Settings
from app.domain.modelos import ConteoEventos
from app.ports.persistencia import EventoYaProcesado

ESQUEMA = "analitica"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {date: Date}


class ConteoEventosFila(Base):
    __tablename__ = "conteo_eventos"
    __table_args__ = (UniqueConstraint("tipo", "fecha", name="uq_conteo_tipo_fecha"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tipo: Mapped[str] = mapped_column(String)
    fecha: Mapped[date]
    cantidad: Mapped[int] = mapped_column(Integer, server_default="0")


class EventoProcesadoFila(Base):
    """Un registro por `evento_id` consumido, para no incrementar dos veces el
    mismo conteo si el mensaje llega repetido (reintento de Kafka, replay)."""

    __tablename__ = "evento_procesado"

    evento_id: Mapped[str] = mapped_column(String, primary_key=True)


def _conteo_a_dominio(fila: ConteoEventosFila) -> ConteoEventos:
    return ConteoEventos(tipo=fila.tipo, fecha=fila.fecha, cantidad=fila.cantidad)


class RepositorioMetricasSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def incrementar(self, evento_id_str: str, tipo: str, fecha: date) -> bool:
        self._s.add(EventoProcesadoFila(evento_id=evento_id_str))
        try:
            await self._s.flush()
        except IntegrityError:
            raise EventoYaProcesado from None

        sentencia = (
            pg_insert(ConteoEventosFila)
            .values(tipo=tipo, fecha=fecha, cantidad=1)
            .on_conflict_do_update(
                index_elements=["tipo", "fecha"],
                set_={"cantidad": ConteoEventosFila.cantidad + 1},
            )
        )
        await self._s.execute(sentencia)
        return True

    async def listar(self, desde: date, hasta: date) -> list[ConteoEventos]:
        filas = await self._s.scalars(
            select(ConteoEventosFila)
            .where(ConteoEventosFila.fecha >= desde, ConteoEventosFila.fecha <= hasta)
            .order_by(ConteoEventosFila.fecha, ConteoEventosFila.tipo)
        )
        return [_conteo_a_dominio(f) for f in filas]


class UnidadDeTrabajoSQL:
    def __init__(self, fabrica: async_sessionmaker[AsyncSession]) -> None:
        self._fabrica = fabrica

    async def __aenter__(self) -> UnidadDeTrabajoSQL:
        self._sesion = self._fabrica()
        self.metricas = RepositorioMetricasSQL(self._sesion)
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._sesion.rollback()
        await self._sesion.close()

    async def confirmar(self) -> None:
        await self._sesion.commit()


def crear_motor(config: Settings) -> AsyncEngine:
    return create_async_engine(config.database_url, pool_size=config.db_pool_size, pool_pre_ping=True)


def fabrica_unidad_de_trabajo(motor: AsyncEngine):
    sesiones = async_sessionmaker(motor, expire_on_commit=False)
    return lambda: UnidadDeTrabajoSQL(sesiones)
