from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any
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
from app.domain.modelos import EstadoSolicitud, EventoDominio, SolicitudCotizacion
from app.domain.oferta import Oferta
from app.domain.rating import ReglaRating
from app.domain.riesgo import OrigenFactorRiesgo
from app.ports.persistencia import ClaveIdempotenciaDuplicada

ESQUEMA = "ms_cotizacion"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class SolicitudFila(Base):
    __tablename__ = "solicitud_cotizacion"

    solicitud_id: Mapped[UUID] = mapped_column("solicitud_id", primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String, unique=True)
    usuario_id: Mapped[UUID]
    socio_id: Mapped[UUID]
    consentimiento_id: Mapped[UUID]
    producto: Mapped[str]
    canal: Mapped[str]
    datos_riesgo: Mapped[dict[str, Any]] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    estado: Mapped[str]
    creada_en: Mapped[datetime]


class ReglaRatingFila(Base):
    __tablename__ = "regla_rating"

    regla_id: Mapped[UUID] = mapped_column(primary_key=True)
    producto: Mapped[str]
    version: Mapped[str]
    formula: Mapped[str]


class OfertaFila(Base):
    __tablename__ = "oferta_seguro"

    oferta_id: Mapped[UUID] = mapped_column(primary_key=True)
    solicitud_id: Mapped[UUID]
    regla_id: Mapped[UUID]
    version_regla: Mapped[str]
    prima: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    prima_neta: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    gastos_expedicion: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    moneda: Mapped[str]
    coberturas: Mapped[str]
    factor_riesgo: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    factor_riesgo_origen: Mapped[str]
    vence_en: Mapped[datetime]


def _oferta_a_dominio(fila: OfertaFila) -> Oferta:
    return Oferta(
        id=fila.oferta_id,
        solicitud_id=fila.solicitud_id,
        regla_id=fila.regla_id,
        version_regla=fila.version_regla,
        prima_neta=fila.prima_neta,
        gastos_expedicion=fila.gastos_expedicion,
        moneda=fila.moneda,
        coberturas=fila.coberturas.split(","),
        factor_riesgo=fila.factor_riesgo,
        factor_riesgo_origen=OrigenFactorRiesgo(fila.factor_riesgo_origen),
        vence_en=fila.vence_en,
    )


class RepositorioOfertasSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener(self, oferta_id: UUID) -> Oferta | None:
        fila = await self._s.get(OfertaFila, oferta_id)
        return _oferta_a_dominio(fila) if fila else None

    async def obtener_por_solicitud(self, solicitud_id: UUID) -> Oferta | None:
        fila = await self._s.scalar(select(OfertaFila).where(OfertaFila.solicitud_id == solicitud_id))
        return _oferta_a_dominio(fila) if fila else None

    async def agregar(self, oferta: Oferta) -> None:
        self._s.add(
            OfertaFila(
                oferta_id=oferta.id,
                solicitud_id=oferta.solicitud_id,
                regla_id=oferta.regla_id,
                version_regla=oferta.version_regla,
                prima=oferta.prima,
                prima_neta=oferta.prima_neta,
                gastos_expedicion=oferta.gastos_expedicion,
                moneda=oferta.moneda,
                coberturas=",".join(oferta.coberturas),
                factor_riesgo=oferta.factor_riesgo,
                factor_riesgo_origen=oferta.factor_riesgo_origen.value,
                vence_en=oferta.vence_en,
            )
        )


class OutboxFila(Base):
    __tablename__ = "outbox_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str]
    agregado_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    publicado_en: Mapped[datetime | None]


def _a_dominio(fila: SolicitudFila) -> SolicitudCotizacion:
    return SolicitudCotizacion(
        id=fila.solicitud_id,
        idempotency_key=fila.idempotency_key,
        usuario_id=fila.usuario_id,
        socio_id=fila.socio_id,
        consentimiento_id=fila.consentimiento_id,
        producto=fila.producto,
        canal=fila.canal,
        datos_riesgo=fila.datos_riesgo,
        estado=EstadoSolicitud(fila.estado),
        creada_en=fila.creada_en,
    )


class RepositorioSolicitudesSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener(self, solicitud_id: UUID) -> SolicitudCotizacion | None:
        fila = await self._s.get(SolicitudFila, solicitud_id)
        return _a_dominio(fila) if fila else None

    async def obtener_por_clave(self, idempotency_key: str) -> SolicitudCotizacion | None:
        fila = await self._s.scalar(
            select(SolicitudFila).where(SolicitudFila.idempotency_key == idempotency_key)
        )
        return _a_dominio(fila) if fila else None

    async def agregar(self, solicitud: SolicitudCotizacion) -> None:
        self._s.add(
            SolicitudFila(
                solicitud_id=solicitud.id,
                idempotency_key=solicitud.idempotency_key,
                usuario_id=solicitud.usuario_id,
                socio_id=solicitud.socio_id,
                consentimiento_id=solicitud.consentimiento_id,
                producto=solicitud.producto,
                canal=solicitud.canal,
                datos_riesgo=solicitud.datos_riesgo,
                estado=solicitud.estado.value,
                creada_en=solicitud.creada_en,
            )
        )

    async def actualizar(self, solicitud: SolicitudCotizacion) -> None:
        fila = await self._s.get(SolicitudFila, solicitud.id)
        fila.estado = solicitud.estado.value


class RepositorioReglasRatingSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_vigente(self, producto: str) -> ReglaRating | None:
        fila = await self._s.scalar(
            select(ReglaRatingFila)
            .where(ReglaRatingFila.producto == producto)
            .order_by(ReglaRatingFila.version.desc())
            .limit(1)
        )
        if fila is None:
            return None
        return ReglaRating(id=fila.regla_id, producto=fila.producto, version=fila.version, formula=json.loads(fila.formula))


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
        self.solicitudes = RepositorioSolicitudesSQL(self._sesion)
        self.reglas_rating = RepositorioReglasRatingSQL(self._sesion)
        self.ofertas = RepositorioOfertasSQL(self._sesion)
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
