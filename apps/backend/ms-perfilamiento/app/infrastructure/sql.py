from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, MetaData, Numeric, String, func, select
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
    AtributoPerfil,
    Consentimiento,
    EstadoAdaptador,
    EventoDominio,
    FactorInterno,
    Oferta,
    OrigenAdaptador,
)
from app.ports.persistencia import ClaveIdempotenciaDuplicada

ESQUEMA = "ms_perfilamiento"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class ConsentimientoFila(Base):
    __tablename__ = "consentimiento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    cliente_id: Mapped[str] = mapped_column(String, index=True)
    otorgado_en: Mapped[datetime]
    revocado_en: Mapped[datetime | None]


class OfertaFila(Base):
    __tablename__ = "oferta"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    idempotency_key: Mapped[str] = mapped_column(String, unique=True)
    cliente_id: Mapped[str] = mapped_column(String, index=True)
    precio: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    moneda: Mapped[str]
    degradado: Mapped[bool] = mapped_column(Boolean)
    factores: Mapped[list] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    snapshot_atributos: Mapped[list] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime]


class OutboxFila(Base):
    __tablename__ = "outbox_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str]
    agregado_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    publicado_en: Mapped[datetime | None]


def _consentimiento_a_dominio(fila: ConsentimientoFila) -> Consentimiento:
    return Consentimiento(
        id=fila.id,
        cliente_id=fila.cliente_id,
        otorgado_en=fila.otorgado_en,
        revocado_en=fila.revocado_en,
    )


def _atributo_a_json(atributo: AtributoPerfil) -> dict:
    return {
        "nombre": atributo.nombre,
        "valor": str(atributo.valor),
        "origen": atributo.origen.value,
        "estado": atributo.estado.value,
        "degradado": atributo.degradado,
    }


def _atributo_desde_json(datos: dict) -> AtributoPerfil:
    return AtributoPerfil(
        nombre=datos["nombre"],
        valor=Decimal(datos["valor"]),
        origen=OrigenAdaptador(datos["origen"]),
        estado=EstadoAdaptador(datos["estado"]),
        degradado=datos["degradado"],
    )


def _factor_a_json(factor: FactorInterno) -> dict:
    return {"factor": factor.factor, "impacto": factor.impacto, "peso": str(factor.peso)}


def _factor_desde_json(datos: dict) -> FactorInterno:
    return FactorInterno(factor=datos["factor"], impacto=datos["impacto"], peso=Decimal(datos["peso"]))


def _oferta_a_dominio(fila: OfertaFila) -> Oferta:
    return Oferta(
        id=fila.id,
        cliente_id=fila.cliente_id,
        precio=fila.precio,
        moneda=fila.moneda,
        factores=tuple(_factor_desde_json(f) for f in fila.factores),
        degradado=fila.degradado,
        snapshot_atributos=tuple(_atributo_desde_json(a) for a in fila.snapshot_atributos),
        creado_en=fila.creado_en,
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
        return _consentimiento_a_dominio(fila) if fila else None

    async def obtener_por_id(self, consentimiento_id: UUID) -> Consentimiento | None:
        fila = await self._s.get(ConsentimientoFila, consentimiento_id)
        return _consentimiento_a_dominio(fila) if fila else None

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
        fila.revocado_en = consentimiento.revocado_en


class RepositorioOfertasSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener(self, oferta_id: UUID) -> Oferta | None:
        fila = await self._s.get(OfertaFila, oferta_id)
        return _oferta_a_dominio(fila) if fila else None

    async def obtener_por_clave(self, idempotency_key: str) -> Oferta | None:
        fila = await self._s.scalar(select(OfertaFila).where(OfertaFila.idempotency_key == idempotency_key))
        return _oferta_a_dominio(fila) if fila else None

    async def obtener_ultima_por_cliente(self, cliente_id: str) -> Oferta | None:
        fila = await self._s.scalar(
            select(OfertaFila)
            .where(OfertaFila.cliente_id == cliente_id)
            .order_by(OfertaFila.creado_en.desc())
            .limit(1)
        )
        return _oferta_a_dominio(fila) if fila else None

    async def agregar(self, idempotency_key: str, oferta: Oferta) -> None:
        self._s.add(
            OfertaFila(
                id=oferta.id,
                idempotency_key=idempotency_key,
                cliente_id=oferta.cliente_id,
                precio=oferta.precio,
                moneda=oferta.moneda,
                degradado=oferta.degradado,
                factores=[_factor_a_json(f) for f in oferta.factores],
                snapshot_atributos=[_atributo_a_json(a) for a in oferta.snapshot_atributos],
                creado_en=oferta.creado_en,
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
        self.consentimientos = RepositorioConsentimientosSQL(self._sesion)
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
