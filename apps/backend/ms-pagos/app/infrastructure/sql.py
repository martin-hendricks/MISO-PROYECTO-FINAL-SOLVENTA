from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    MetaData,
    Numeric,
    String,
    func,
    select,
)
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
from app.domain.modelos import CONCEPTO_PRIMA, EstadoPago, EventoDominio, Pago
from app.ports.persistencia import ClaveIdempotenciaDuplicada

ESQUEMA = "ms_pagos"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class MedioPagoFila(Base):
    __tablename__ = "medio_pago"

    medio_pago_id: Mapped[UUID] = mapped_column(primary_key=True)
    usuario_id: Mapped[UUID]
    tipo: Mapped[str]
    token_referencia: Mapped[str]


class PagoFila(Base):
    __tablename__ = "pago"

    pago_id: Mapped[UUID] = mapped_column(primary_key=True)
    medio_pago_id: Mapped[UUID] = mapped_column(ForeignKey(MedioPagoFila.medio_pago_id))
    oferta_id: Mapped[UUID | None]
    prima_id: Mapped[UUID | None]
    reclamacion_id: Mapped[UUID | None]
    monto: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    concepto: Mapped[str]
    estado: Mapped[str]
    fecha: Mapped[datetime]


class TransaccionFila(Base):
    __tablename__ = "transaccion_pasarela"

    transaccion_id: Mapped[UUID] = mapped_column(primary_key=True)
    pago_id: Mapped[UUID] = mapped_column(ForeignKey(PagoFila.pago_id))
    proveedor: Mapped[str]
    referencia_externa: Mapped[str | None] = mapped_column(String)
    estado: Mapped[str]
    idempotency_key: Mapped[str] = mapped_column(String, unique=True)


class OutboxFila(Base):
    __tablename__ = "outbox_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str]
    agregado_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    publicado_en: Mapped[datetime | None]


def _a_dominio(pago: PagoFila, transaccion: TransaccionFila, medio: MedioPagoFila) -> Pago:
    return Pago(
        id=pago.pago_id,
        oferta_id=pago.oferta_id,
        usuario_id=medio.usuario_id,
        monto=pago.monto,
        estado=EstadoPago(pago.estado),
        idempotency_key=transaccion.idempotency_key,
        proveedor=transaccion.proveedor,
        referencia_externa=transaccion.referencia_externa or "",
        fecha=pago.fecha,
    )


_CONSULTA = (
    select(PagoFila, TransaccionFila, MedioPagoFila)
    .join(TransaccionFila, TransaccionFila.pago_id == PagoFila.pago_id)
    .join(MedioPagoFila, MedioPagoFila.medio_pago_id == PagoFila.medio_pago_id)
)


class RepositorioPagosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def _uno(self, consulta) -> Pago | None:
        fila = (await self._s.execute(consulta)).first()
        return _a_dominio(*fila) if fila else None

    async def obtener(self, pago_id: UUID) -> Pago | None:
        return await self._uno(_CONSULTA.where(PagoFila.pago_id == pago_id))

    async def obtener_por_clave(self, idempotency_key: str) -> Pago | None:
        return await self._uno(_CONSULTA.where(TransaccionFila.idempotency_key == idempotency_key))

    async def agregar(self, pago: Pago, token_medio_pago: str) -> None:
        medio_pago_id = uuid4()
        self._s.add(
            MedioPagoFila(
                medio_pago_id=medio_pago_id,
                usuario_id=pago.usuario_id,
                tipo="TOKEN",
                token_referencia=token_medio_pago,
            )
        )
        self._s.add(
            PagoFila(
                pago_id=pago.id,
                medio_pago_id=medio_pago_id,
                oferta_id=pago.oferta_id,
                monto=pago.monto,
                concepto=CONCEPTO_PRIMA,
                estado=pago.estado.value,
                fecha=pago.fecha,
            )
        )
        self._s.add(
            TransaccionFila(
                transaccion_id=uuid4(),
                pago_id=pago.id,
                proveedor=pago.proveedor,
                referencia_externa=pago.referencia_externa,
                estado=pago.estado.value,
                idempotency_key=pago.idempotency_key,
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
            if "uq_transaccion_idempotency" in str(exc.orig):
                raise ClaveIdempotenciaDuplicada from exc
            raise


def crear_motor(config: Settings) -> AsyncEngine:
    return create_async_engine(config.database_url, pool_size=config.db_pool_size, pool_pre_ping=True)


def fabrica_unidad_de_trabajo(motor: AsyncEngine):
    sesiones = async_sessionmaker(motor, expire_on_commit=False)
    return lambda: UnidadDeTrabajoSQL(sesiones)
