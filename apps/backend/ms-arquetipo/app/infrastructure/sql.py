from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, MetaData, Numeric, String, func, select
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
from app.domain.modelos import Ejemplo, EstadoEjemplo, EventoDominio
from app.ports.persistencia import ClaveIdempotenciaDuplicada

ESQUEMA = "ms_arquetipo"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)


class EjemploFila(Base):
    __tablename__ = "ejemplo"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String, unique=True)
    referencia: Mapped[str]
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    estado: Mapped[str]
    creado_en: Mapped[datetime]


class OutboxFila(Base):
    __tablename__ = "outbox_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str]
    agregado_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    publicado_en: Mapped[datetime | None]


def _a_dominio(fila: EjemploFila) -> Ejemplo:
    return Ejemplo(
        id=fila.id,
        idempotency_key=fila.idempotency_key,
        referencia=fila.referencia,
        monto=fila.monto,
        estado=EstadoEjemplo(fila.estado),
        creado_en=fila.creado_en,
    )


class RepositorioEjemplosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener(self, ejemplo_id: UUID) -> Ejemplo | None:
        fila = await self._s.get(EjemploFila, ejemplo_id)
        return _a_dominio(fila) if fila else None

    async def obtener_por_clave(self, idempotency_key: str) -> Ejemplo | None:
        fila = await self._s.scalar(select(EjemploFila).where(EjemploFila.idempotency_key == idempotency_key))
        return _a_dominio(fila) if fila else None

    async def listar(self, limite: int) -> list[Ejemplo]:
        filas = await self._s.scalars(select(EjemploFila).order_by(EjemploFila.creado_en.desc()).limit(limite))
        return [_a_dominio(f) for f in filas]

    async def indicadores(self) -> tuple[int, Decimal]:
        total, monto = (
            await self._s.execute(select(func.count(), func.coalesce(func.sum(EjemploFila.monto), 0)))
        ).one()
        return total, Decimal(monto)

    async def agregar(self, ejemplo: Ejemplo) -> None:
        self._s.add(
            EjemploFila(
                id=ejemplo.id,
                idempotency_key=ejemplo.idempotency_key,
                referencia=ejemplo.referencia,
                monto=ejemplo.monto,
                estado=ejemplo.estado.value,
                creado_en=ejemplo.creado_en,
            )
        )

    async def actualizar(self, ejemplo: Ejemplo) -> None:
        fila = await self._s.get(EjemploFila, ejemplo.id)
        fila.estado = ejemplo.estado.value


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
        self.ejemplos = RepositorioEjemplosSQL(self._sesion)
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
            if "idempotency_key" in str(exc.orig):
                raise ClaveIdempotenciaDuplicada from exc
            raise


def crear_motor(config: Settings) -> AsyncEngine:
    return create_async_engine(config.database_url, pool_size=config.db_pool_size, pool_pre_ping=True)


def fabrica_unidad_de_trabajo(motor: AsyncEngine):
    sesiones = async_sessionmaker(motor, expire_on_commit=False)
    return lambda: UnidadDeTrabajoSQL(sesiones)
