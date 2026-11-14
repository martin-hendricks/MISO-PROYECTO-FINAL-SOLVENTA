from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Index, Integer, MetaData, String, UniqueConstraint, func, select
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
from app.domain.modelos import Difusion, DispositivoPush, EstadoNotificacion, Notificacion
from app.ports.persistencia import DispositivoDuplicado, NotificacionDuplicada

ESQUEMA = "notificaciones"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class NotificacionFila(Base):
    __tablename__ = "notificacion"
    __table_args__ = (
        UniqueConstraint("evento_origen_id", "canal", name="uq_notificacion_evento_canal"),
        Index("ix_notificacion_usuario", "usuario_id", "creada_en"),
    )

    notificacion_id: Mapped[UUID] = mapped_column(primary_key=True)
    usuario_id: Mapped[UUID]
    evento_origen_id: Mapped[UUID | None]
    canal: Mapped[str] = mapped_column(String)
    tipo: Mapped[str] = mapped_column(String)
    titulo: Mapped[str] = mapped_column(String)
    cuerpo: Mapped[str] = mapped_column(String)
    destino: Mapped[str | None]
    poliza: Mapped[str | None]
    difusion_id: Mapped[UUID | None]
    estado: Mapped[str] = mapped_column(String)
    creada_en: Mapped[datetime] = mapped_column(server_default=func.now())
    enviada_en: Mapped[datetime | None]
    leida_en: Mapped[datetime | None]
    proveedor_id: Mapped[str | None]


class DispositivoPushFila(Base):
    __tablename__ = "dispositivo_push"
    __table_args__ = (
        UniqueConstraint("usuario_id", "token", name="uq_dispositivo_usuario_token"),
        Index("ix_dispositivo_usuario", "usuario_id", "activo"),
    )

    dispositivo_id: Mapped[UUID] = mapped_column(primary_key=True)
    usuario_id: Mapped[UUID]
    plataforma: Mapped[str] = mapped_column(String)
    token: Mapped[str] = mapped_column(String)
    activo: Mapped[bool] = mapped_column(Boolean, server_default="true")
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    actualizado_en: Mapped[datetime] = mapped_column(server_default=func.now())


def _notificacion_a_dominio(fila: NotificacionFila) -> Notificacion:
    return Notificacion(
        notificacion_id=fila.notificacion_id,
        usuario_id=fila.usuario_id,
        evento_origen_id=fila.evento_origen_id,
        canal=fila.canal,
        tipo=fila.tipo,
        titulo=fila.titulo,
        cuerpo=fila.cuerpo,
        destino=fila.destino,
        poliza=fila.poliza,
        difusion_id=fila.difusion_id,
        estado=fila.estado,
        creada_en=fila.creada_en,
        enviada_en=fila.enviada_en,
        leida_en=fila.leida_en,
        proveedor_id=fila.proveedor_id,
    )


def _dispositivo_a_dominio(fila: DispositivoPushFila) -> DispositivoPush:
    return DispositivoPush(
        dispositivo_id=fila.dispositivo_id,
        usuario_id=fila.usuario_id,
        plataforma=fila.plataforma,
        token=fila.token,
        activo=fila.activo,
        creado_en=fila.creado_en,
        actualizado_en=fila.actualizado_en,
    )


class RepositorioNotificacionesSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener(self, notificacion_id: UUID) -> Notificacion | None:
        fila = await self._s.get(NotificacionFila, notificacion_id)
        return _notificacion_a_dominio(fila) if fila else None

    async def obtener_por_evento_canal(
        self, evento_origen_id: UUID, canal: str
    ) -> Notificacion | None:
        fila = await self._s.scalar(
            select(NotificacionFila).where(
                NotificacionFila.evento_origen_id == evento_origen_id,
                NotificacionFila.canal == canal,
            )
        )
        return _notificacion_a_dominio(fila) if fila else None

    async def listar(
        self, usuario_id: UUID, limite: int, antes_de: datetime | None = None
    ) -> list[Notificacion]:
        consulta = select(NotificacionFila).where(NotificacionFila.usuario_id == usuario_id)
        if antes_de is not None:
            consulta = consulta.where(NotificacionFila.creada_en < antes_de)
        filas = await self._s.scalars(
            consulta.order_by(NotificacionFila.creada_en.desc()).limit(limite)
        )
        return [_notificacion_a_dominio(f) for f in filas]

    async def listar_pendientes_push(
        self, usuario_id: UUID | None = None, limite: int = 100
    ) -> list[Notificacion]:
        consulta = select(NotificacionFila).where(
            NotificacionFila.estado == EstadoNotificacion.PENDIENTE.value,
            NotificacionFila.canal == "push",
        )
        if usuario_id is not None:
            consulta = consulta.where(NotificacionFila.usuario_id == usuario_id)
        filas = await self._s.scalars(
            consulta.order_by(NotificacionFila.creada_en.asc()).limit(limite)
        )
        return [_notificacion_a_dominio(f) for f in filas]

    async def agregar(self, notificacion: Notificacion) -> None:
        self._s.add(
            NotificacionFila(
                notificacion_id=notificacion.notificacion_id,
                usuario_id=notificacion.usuario_id,
                evento_origen_id=notificacion.evento_origen_id,
                canal=notificacion.canal,
                tipo=notificacion.tipo,
                titulo=notificacion.titulo,
                cuerpo=notificacion.cuerpo,
                destino=notificacion.destino,
                poliza=notificacion.poliza,
                difusion_id=notificacion.difusion_id,
                estado=notificacion.estado,
                creada_en=notificacion.creada_en,
                enviada_en=notificacion.enviada_en,
                leida_en=notificacion.leida_en,
                proveedor_id=notificacion.proveedor_id,
            )
        )

    async def actualizar(self, notificacion: Notificacion) -> None:
        fila = await self._s.get(NotificacionFila, notificacion.notificacion_id)
        if fila is None:
            raise RuntimeError(f"Notificación {notificacion.notificacion_id} no persistida")
        fila.estado = notificacion.estado
        fila.enviada_en = notificacion.enviada_en
        fila.leida_en = notificacion.leida_en
        fila.proveedor_id = notificacion.proveedor_id


class RepositorioDispositivosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener(self, dispositivo_id: UUID) -> DispositivoPush | None:
        fila = await self._s.get(DispositivoPushFila, dispositivo_id)
        return _dispositivo_a_dominio(fila) if fila else None

    async def obtener_por_usuario_token(
        self, usuario_id: UUID, token: str
    ) -> DispositivoPush | None:
        fila = await self._s.scalar(
            select(DispositivoPushFila).where(
                DispositivoPushFila.usuario_id == usuario_id,
                DispositivoPushFila.token == token,
            )
        )
        return _dispositivo_a_dominio(fila) if fila else None

    async def listar_activos(self, usuario_id: UUID) -> list[DispositivoPush]:
        filas = await self._s.scalars(
            select(DispositivoPushFila).where(
                DispositivoPushFila.usuario_id == usuario_id,
                DispositivoPushFila.activo.is_(True),
            )
        )
        return [_dispositivo_a_dominio(f) for f in filas]

    async def agregar(self, dispositivo: DispositivoPush) -> None:
        self._s.add(
            DispositivoPushFila(
                dispositivo_id=dispositivo.dispositivo_id,
                usuario_id=dispositivo.usuario_id,
                plataforma=dispositivo.plataforma,
                token=dispositivo.token,
                activo=dispositivo.activo,
                creado_en=dispositivo.creado_en,
                actualizado_en=dispositivo.actualizado_en,
            )
        )

    async def actualizar(self, dispositivo: DispositivoPush) -> None:
        fila = await self._s.get(DispositivoPushFila, dispositivo.dispositivo_id)
        if fila is None:
            raise RuntimeError(f"Dispositivo {dispositivo.dispositivo_id} no persistido")
        fila.plataforma = dispositivo.plataforma
        fila.activo = dispositivo.activo
        fila.actualizado_en = dispositivo.actualizado_en

    async def contar_activos(self, usuario_ids: list[UUID] | None) -> list[tuple[UUID, int]]:
        consulta = select(DispositivoPushFila.usuario_id, func.count()).where(
            DispositivoPushFila.activo.is_(True)
        )
        if usuario_ids is not None:
            consulta = consulta.where(DispositivoPushFila.usuario_id.in_(usuario_ids))
        consulta = consulta.group_by(DispositivoPushFila.usuario_id)
        filas = await self._s.execute(consulta)
        return [(usuario_id, int(cantidad)) for usuario_id, cantidad in filas.all()]

    async def desactivar_de_usuario(self, usuario_id: UUID) -> None:
        filas = await self._s.scalars(
            select(DispositivoPushFila).where(
                DispositivoPushFila.usuario_id == usuario_id,
                DispositivoPushFila.activo.is_(True),
            )
        )
        momento = datetime.now(UTC)
        for fila in filas:
            fila.activo = False
            fila.actualizado_en = momento


class DifusionFila(Base):
    __tablename__ = "difusion"
    __table_args__ = (Index("ix_difusion_creada", "creada_en"),)

    difusion_id: Mapped[UUID] = mapped_column(primary_key=True)
    autor_id: Mapped[UUID]
    titulo: Mapped[str] = mapped_column(String)
    cuerpo: Mapped[str] = mapped_column(String)
    poliza: Mapped[str | None]
    audiencia: Mapped[str] = mapped_column(String)
    destinatarios: Mapped[int] = mapped_column(Integer)
    enviadas: Mapped[int] = mapped_column(Integer, default=0)
    fallidas: Mapped[int] = mapped_column(Integer, default=0)
    sin_dispositivo: Mapped[int] = mapped_column(Integer, default=0)
    creada_en: Mapped[datetime] = mapped_column(server_default=func.now())


class EventoConsumidoFila(Base):
    __tablename__ = "evento_consumido"

    evento_id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str] = mapped_column(String)
    procesado_en: Mapped[datetime] = mapped_column(server_default=func.now())


def _difusion_a_dominio(fila: DifusionFila) -> Difusion:
    return Difusion(
        difusion_id=fila.difusion_id,
        autor_id=fila.autor_id,
        titulo=fila.titulo,
        cuerpo=fila.cuerpo,
        poliza=fila.poliza,
        audiencia=fila.audiencia,
        destinatarios=fila.destinatarios,
        enviadas=fila.enviadas,
        fallidas=fila.fallidas,
        sin_dispositivo=fila.sin_dispositivo,
        creada_en=fila.creada_en,
    )


class RepositorioDifusionesSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def agregar(self, difusion: Difusion) -> None:
        self._s.add(
            DifusionFila(
                difusion_id=difusion.difusion_id,
                autor_id=difusion.autor_id,
                titulo=difusion.titulo,
                cuerpo=difusion.cuerpo,
                poliza=difusion.poliza,
                audiencia=difusion.audiencia,
                destinatarios=difusion.destinatarios,
                enviadas=difusion.enviadas,
                fallidas=difusion.fallidas,
                sin_dispositivo=difusion.sin_dispositivo,
                creada_en=difusion.creada_en,
            )
        )

    async def actualizar_totales(self, difusion_id, enviadas, fallidas, sin_dispositivo) -> None:
        fila = await self._s.get(DifusionFila, difusion_id)
        if fila is None:
            raise RuntimeError(f"Difusión {difusion_id} no persistida")
        fila.enviadas = enviadas
        fila.fallidas = fallidas
        fila.sin_dispositivo = sin_dispositivo

    async def listar(self, limite: int, antes_de: datetime | None = None) -> list[Difusion]:
        consulta = select(DifusionFila)
        if antes_de is not None:
            consulta = consulta.where(DifusionFila.creada_en < antes_de)
        filas = await self._s.scalars(
            consulta.order_by(DifusionFila.creada_en.desc()).limit(limite)
        )
        return [_difusion_a_dominio(fila) for fila in filas]


class RepositorioEventosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def consumir(self, evento_id: UUID, tipo: str) -> bool:
        resultado = await self._s.execute(
            pg_insert(EventoConsumidoFila)
            .values(evento_id=evento_id, tipo=tipo, procesado_en=datetime.now(UTC))
            .on_conflict_do_nothing(index_elements=[EventoConsumidoFila.evento_id])
        )
        return resultado.rowcount == 1


class UnidadDeTrabajoSQL:
    def __init__(self, fabrica: async_sessionmaker[AsyncSession]) -> None:
        self._fabrica = fabrica

    async def __aenter__(self) -> UnidadDeTrabajoSQL:
        self._sesion = self._fabrica()
        self.notificaciones = RepositorioNotificacionesSQL(self._sesion)
        self.dispositivos = RepositorioDispositivosSQL(self._sesion)
        self.difusiones = RepositorioDifusionesSQL(self._sesion)
        self.eventos = RepositorioEventosSQL(self._sesion)
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self._sesion.rollback()
        await self._sesion.close()

    async def confirmar(self) -> None:
        try:
            await self._sesion.commit()
        except IntegrityError as exc:
            await self._sesion.rollback()
            detalle = str(exc.orig)
            if "uq_notificacion_evento_canal" in detalle:
                raise NotificacionDuplicada from exc
            if "uq_dispositivo_usuario_token" in detalle:
                raise DispositivoDuplicado from exc
            raise


def crear_motor(config: Settings) -> AsyncEngine:
    return create_async_engine(config.database_url, pool_size=config.db_pool_size, pool_pre_ping=True)


def fabrica_unidad_de_trabajo(motor: AsyncEngine):
    sesiones = async_sessionmaker(motor, expire_on_commit=False)
    return lambda: UnidadDeTrabajoSQL(sesiones)
