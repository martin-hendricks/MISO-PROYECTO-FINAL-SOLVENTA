from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, MetaData, String, select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import Settings
from app.domain.modelos import Consentimiento

ESQUEMA = "ms_consentimiento"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class ConsentimientoFila(Base):
    __tablename__ = "consentimiento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[str] = mapped_column(String, index=True)
    otorgado_en: Mapped[datetime]
    revocado_en: Mapped[datetime | None]


def _a_dominio(fila: ConsentimientoFila) -> Consentimiento:
    return Consentimiento(
        id=fila.id,
        cliente_id=fila.cliente_id,
        otorgado_en=fila.otorgado_en,
        revocado_en=fila.revocado_en,
    )


class RepositorioConsentimientosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_vigente(self, cliente_id: str) -> Consentimiento | None:
        fila = await self._s.scalar(
            select(ConsentimientoFila)
            .where(ConsentimientoFila.cliente_id == cliente_id, ConsentimientoFila.revocado_en.is_(None))
            .order_by(ConsentimientoFila.otorgado_en.desc())
        )
        return _a_dominio(fila) if fila else None

    async def obtener_por_id(self, consentimiento_id: UUID) -> Consentimiento | None:
        fila = await self._s.get(ConsentimientoFila, consentimiento_id)
        return _a_dominio(fila) if fila else None

    async def agregar(self, consentimiento: Consentimiento) -> None:
        self._s.add(
            ConsentimientoFila(
                id=consentimiento.id,
                cliente_id=consentimiento.cliente_id,
                otorgado_en=consentimiento.otorgado_en,
                revocado_en=consentimiento.revocado_en,
            )
        )

    async def actualizar(self, consentimiento: Consentimiento) -> None:
        fila = await self._s.get(ConsentimientoFila, consentimiento.id)
        if fila is not None:
            fila.revocado_en = consentimiento.revocado_en


class UnidadDeTrabajoSQL:
    def __init__(self, fabrica: async_sessionmaker[AsyncSession]) -> None:
        self._fabrica = fabrica

    async def __aenter__(self) -> UnidadDeTrabajoSQL:
        self._sesion = self._fabrica()
        self.consentimientos = RepositorioConsentimientosSQL(self._sesion)
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
