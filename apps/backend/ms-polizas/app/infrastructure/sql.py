from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    MetaData,
    Numeric,
    Sequence,
    String,
    desc,
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
from app.domain.modelos import Cobertura, EstadoPoliza, EventoDominio, Poliza
from app.ports.persistencia import PolizaYaEmitida

ESQUEMA = "ms_polizas"

SECUENCIA_NUMERO = Sequence("poliza_numero_seq", schema=ESQUEMA)


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class PolizaFila(Base):
    __tablename__ = "poliza"

    poliza_id: Mapped[UUID] = mapped_column(primary_key=True)
    oferta_id: Mapped[UUID] = mapped_column(unique=True)
    usuario_id: Mapped[UUID]
    numero: Mapped[str] = mapped_column(String, unique=True)
    inicio_vigencia: Mapped[date]
    fin_vigencia: Mapped[date]
    estado: Mapped[str]
    firma_hash: Mapped[str | None] = mapped_column(String)


class CoberturaFila(Base):
    __tablename__ = "cobertura"

    cobertura_id: Mapped[UUID] = mapped_column(primary_key=True)
    poliza_id: Mapped[UUID] = mapped_column(ForeignKey(PolizaFila.poliza_id))
    nombre: Mapped[str]
    suma_asegurada: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    deducible: Mapped[Decimal] = mapped_column(Numeric(14, 2))


class OutboxFila(Base):
    __tablename__ = "outbox_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str]
    agregado_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    publicado_en: Mapped[datetime | None]


def _a_dominio(fila: PolizaFila, coberturas: list[CoberturaFila]) -> Poliza:
    return Poliza(
        id=fila.poliza_id,
        oferta_id=fila.oferta_id,
        usuario_id=fila.usuario_id,
        numero=fila.numero,
        inicio_vigencia=fila.inicio_vigencia,
        fin_vigencia=fila.fin_vigencia,
        estado=EstadoPoliza(fila.estado),
        coberturas=tuple(
            Cobertura(nombre=c.nombre, suma_asegurada=c.suma_asegurada, deducible=c.deducible) for c in coberturas
        ),
    )


class RepositorioPolizasSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def _con_coberturas(self, fila: PolizaFila | None) -> Poliza | None:
        if fila is None:
            return None
        coberturas = await self._s.scalars(
            select(CoberturaFila).where(CoberturaFila.poliza_id == fila.poliza_id).order_by(CoberturaFila.nombre)
        )
        return _a_dominio(fila, list(coberturas))

    async def obtener(self, poliza_id: UUID) -> Poliza | None:
        return await self._con_coberturas(await self._s.scalar(select(PolizaFila).where(PolizaFila.poliza_id == poliza_id)))

    async def obtener_por_oferta(self, oferta_id: UUID) -> Poliza | None:
        return await self._con_coberturas(await self._s.scalar(select(PolizaFila).where(PolizaFila.oferta_id == oferta_id)))

    async def obtener_por_numero(self, numero: str) -> Poliza | None:
        return await self._con_coberturas(await self._s.scalar(select(PolizaFila).where(PolizaFila.numero == numero)))

    async def listar_por_usuario(self, usuario_id: UUID, limite: int) -> list[Poliza]:
        filas = await self._s.scalars(
            select(PolizaFila)
            .where(PolizaFila.usuario_id == usuario_id)
            .order_by(desc(PolizaFila.inicio_vigencia))
            .limit(limite)
        )
        return [await self._con_coberturas(fila) for fila in filas]

    async def siguiente_secuencia(self) -> int:
        return int(await self._s.scalar(SECUENCIA_NUMERO.next_value()))

    async def agregar(self, poliza: Poliza) -> None:
        self._s.add(
            PolizaFila(
                poliza_id=poliza.id,
                oferta_id=poliza.oferta_id,
                usuario_id=poliza.usuario_id,
                numero=poliza.numero,
                inicio_vigencia=poliza.inicio_vigencia,
                fin_vigencia=poliza.fin_vigencia,
                estado=poliza.estado.value,
            )
        )
        for cobertura in poliza.coberturas:
            self._s.add(
                CoberturaFila(
                    cobertura_id=uuid4(),
                    poliza_id=poliza.id,
                    nombre=cobertura.nombre,
                    suma_asegurada=cobertura.suma_asegurada,
                    deducible=cobertura.deducible,
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
        self.polizas = RepositorioPolizasSQL(self._sesion)
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
            if "uq_poliza_oferta" in str(exc.orig):
                raise PolizaYaEmitida from exc
            raise


def crear_motor(config: Settings) -> AsyncEngine:
    return create_async_engine(config.database_url, pool_size=config.db_pool_size, pool_pre_ping=True)


def fabrica_unidad_de_trabajo(motor: AsyncEngine):
    sesiones = async_sessionmaker(motor, expire_on_commit=False)
    return lambda: UnidadDeTrabajoSQL(sesiones)
