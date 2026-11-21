from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    MetaData,
    Numeric,
    String,
    func,
    or_,
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
from app.domain.modelos import EstadoUsuario, EventoDominio, Usuario
from app.domain.socios import CredencialSocio, EstadoSocio, Socio
from app.ports.persistencia import TAMANO_PAGINA_CLIENTES, CuentaYaExiste

ESQUEMA = "ms_identidad"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)
    type_annotation_map = {datetime: DateTime(timezone=True)}


class UsuarioFila(Base):
    __tablename__ = "usuario"

    usuario_id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo_documento: Mapped[str] = mapped_column(String)
    numero_documento: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)
    estado: Mapped[str] = mapped_column(String)
    nombre: Mapped[str] = mapped_column(String, default="")
    apellidos: Mapped[str] = mapped_column(String, default="")
    ingresos_mensuales: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    gastos_mensuales: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    rol: Mapped[str] = mapped_column(String, default="cliente")
    prueba_de_vida: Mapped[str] = mapped_column(String, default="no")
    canal: Mapped[str | None] = mapped_column(String, default=None)


class OutboxFila(Base):
    __tablename__ = "outbox_evento"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo: Mapped[str]
    agregado_id: Mapped[UUID]
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    creado_en: Mapped[datetime] = mapped_column(server_default=func.now())
    publicado_en: Mapped[datetime | None]


class SocioFila(Base):
    __tablename__ = "socio"

    socio_id: Mapped[UUID] = mapped_column(primary_key=True)
    nombre: Mapped[str] = mapped_column(String)
    alcances: Mapped[list] = mapped_column(JSON().with_variant(JSONB(), "postgresql"))
    estado: Mapped[str] = mapped_column(String)
    creado_en: Mapped[datetime]


class CredencialSocioFila(Base):
    __tablename__ = "credencial_socio"

    credencial_id: Mapped[UUID] = mapped_column(primary_key=True)
    socio_id: Mapped[UUID] = mapped_column(ForeignKey(f"{ESQUEMA}.socio.socio_id"))
    huella_sha256: Mapped[str] = mapped_column(String)
    creada_en: Mapped[datetime]
    revocada_en: Mapped[datetime | None]


def _fila(usuario: Usuario) -> UsuarioFila:
    return UsuarioFila(
        usuario_id=usuario.id,
        tipo_documento=usuario.tipo_documento,
        numero_documento=usuario.numero_documento,
        email=usuario.email,
        password_hash=usuario.password_hash,
        estado=usuario.estado.value,
        nombre=usuario.nombre,
        apellidos=usuario.apellidos,
        ingresos_mensuales=usuario.ingresos_mensuales,
        gastos_mensuales=usuario.gastos_mensuales,
        rol=usuario.rol,
        prueba_de_vida=usuario.prueba_de_vida,
        canal=usuario.canal,
    )


def _a_dominio(fila: UsuarioFila) -> Usuario:
    return Usuario(
        id=fila.usuario_id,
        tipo_documento=fila.tipo_documento,
        numero_documento=fila.numero_documento,
        email=fila.email,
        password_hash=fila.password_hash,
        estado=EstadoUsuario(fila.estado),
        nombre=fila.nombre or "",
        apellidos=fila.apellidos or "",
        ingresos_mensuales=fila.ingresos_mensuales,
        gastos_mensuales=fila.gastos_mensuales,
        rol=getattr(fila, "rol", None) or "cliente",
        prueba_de_vida=getattr(fila, "prueba_de_vida", None) or "no",
        canal=getattr(fila, "canal", None),
    )


class RepositorioUsuariosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def obtener_por_email(self, email: str) -> Usuario | None:
        fila = await self._s.scalar(select(UsuarioFila).where(func.lower(UsuarioFila.email) == email.lower()))
        return _a_dominio(fila) if fila else None

    async def obtener_por_documento(self, tipo_documento: str, numero_documento: str) -> Usuario | None:
        fila = await self._s.scalar(
            select(UsuarioFila).where(
                UsuarioFila.tipo_documento == tipo_documento,
                UsuarioFila.numero_documento == numero_documento,
            )
        )
        return _a_dominio(fila) if fila else None

    async def obtener_por_id(self, usuario_id: UUID) -> Usuario | None:
        fila = await self._s.get(UsuarioFila, usuario_id)
        return _a_dominio(fila) if fila else None

    async def agregar(self, usuario: Usuario) -> None:
        self._s.add(_fila(usuario))

    async def actualizar(self, usuario: Usuario) -> None:
        fila = await self._s.get(UsuarioFila, usuario.id)
        if fila is None:
            return
        fila.nombre = usuario.nombre
        fila.apellidos = usuario.apellidos
        fila.ingresos_mensuales = usuario.ingresos_mensuales
        fila.gastos_mensuales = usuario.gastos_mensuales
        fila.email = usuario.email
        fila.estado = usuario.estado.value
        fila.prueba_de_vida = usuario.prueba_de_vida

    async def listar_clientes(
        self,
        estado: str | None,
        q: str | None,
        ids: list[UUID] | None,
        pagina: int,
    ) -> tuple[list[Usuario], bool]:
        tamano = len(ids) if ids else TAMANO_PAGINA_CLIENTES
        consulta = select(UsuarioFila).where(UsuarioFila.rol == "cliente")
        if estado:
            consulta = consulta.where(UsuarioFila.estado == estado)
        if q:
            patron = _patron_ilike(q)
            consulta = consulta.where(
                or_(
                    UsuarioFila.nombre.ilike(patron, escape="\\"),
                    UsuarioFila.apellidos.ilike(patron, escape="\\"),
                    UsuarioFila.email.ilike(patron, escape="\\"),
                    UsuarioFila.numero_documento.ilike(patron, escape="\\"),
                )
            )
        if ids:
            consulta = consulta.where(UsuarioFila.usuario_id.in_(ids))
        consulta = (
            consulta.order_by(UsuarioFila.apellidos, UsuarioFila.nombre, UsuarioFila.usuario_id)
            .offset((pagina - 1) * tamano)
            .limit(tamano + 1)
        )
        filas = (await self._s.scalars(consulta)).all()
        hay_mas = len(filas) > tamano
        return [_a_dominio(fila) for fila in filas[:tamano]], hay_mas

    async def listar_por_rol(self, rol: str) -> list[Usuario]:
        """Listado del back-office (HU-141): todos los usuarios con ese rol,
        sin paginar -- la cartera de clientes no tiene volumen hoy que lo
        justifique; se agrega paginación cuando haga falta."""
        filas = await self._s.scalars(select(UsuarioFila).where(UsuarioFila.rol == rol))
        return [_a_dominio(fila) for fila in filas]


def _patron_ilike(q: str) -> str:
    escapado = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escapado}%"


def _socio_a_dominio(fila: SocioFila, credenciales: list[CredencialSocioFila]) -> Socio:
    return Socio(
        socio_id=fila.socio_id,
        nombre=fila.nombre,
        alcances=frozenset(fila.alcances),
        estado=EstadoSocio(fila.estado),
        creado_en=fila.creado_en,
        credenciales=[
            CredencialSocio(
                credencial_id=c.credencial_id,
                huella_sha256=c.huella_sha256,
                creada_en=c.creada_en,
                revocada_en=c.revocada_en,
            )
            for c in sorted(credenciales, key=lambda c: (c.creada_en, c.credencial_id))
        ],
    )


class RepositorioSociosSQL:
    def __init__(self, sesion: AsyncSession) -> None:
        self._s = sesion

    async def _credenciales(self, socio_ids: list[UUID]) -> dict[UUID, list[CredencialSocioFila]]:
        por_socio: dict[UUID, list[CredencialSocioFila]] = {i: [] for i in socio_ids}
        if not socio_ids:
            return por_socio
        filas = await self._s.scalars(select(CredencialSocioFila).where(CredencialSocioFila.socio_id.in_(socio_ids)))
        for fila in filas:
            por_socio[fila.socio_id].append(fila)
        return por_socio

    async def agregar(self, socio: Socio) -> None:
        self._s.add(
            SocioFila(
                socio_id=socio.socio_id,
                nombre=socio.nombre,
                alcances=sorted(socio.alcances),
                estado=socio.estado.value,
                creado_en=socio.creado_en,
            )
        )
        await self._s.flush()
        await self._guardar_credenciales(socio)

    async def actualizar(self, socio: Socio) -> None:
        fila = await self._s.get(SocioFila, socio.socio_id)
        if fila is None:
            return
        fila.nombre = socio.nombre
        fila.alcances = sorted(socio.alcances)
        fila.estado = socio.estado.value
        await self._guardar_credenciales(socio)

    async def _guardar_credenciales(self, socio: Socio) -> None:
        existentes = (await self._credenciales([socio.socio_id]))[socio.socio_id]
        por_id = {fila.credencial_id: fila for fila in existentes}
        for credencial in socio.credenciales:
            fila = por_id.get(credencial.credencial_id)
            if fila is None:
                self._s.add(
                    CredencialSocioFila(
                        credencial_id=credencial.credencial_id,
                        socio_id=socio.socio_id,
                        huella_sha256=credencial.huella_sha256,
                        creada_en=credencial.creada_en,
                        revocada_en=credencial.revocada_en,
                    )
                )
            else:
                fila.revocada_en = credencial.revocada_en

    async def obtener(self, socio_id: UUID) -> Socio | None:
        fila = await self._s.get(SocioFila, socio_id)
        if fila is None:
            return None
        return _socio_a_dominio(fila, (await self._credenciales([socio_id]))[socio_id])

    async def obtener_por_huella(self, huella_sha256: str) -> Socio | None:
        socio_id = await self._s.scalar(
            select(CredencialSocioFila.socio_id).where(CredencialSocioFila.huella_sha256 == huella_sha256)
        )
        return await self.obtener(socio_id) if socio_id else None

    async def listar(self) -> list[Socio]:
        filas = list(await self._s.scalars(select(SocioFila).order_by(SocioFila.creado_en, SocioFila.socio_id)))
        credenciales = await self._credenciales([f.socio_id for f in filas])
        return [_socio_a_dominio(f, credenciales[f.socio_id]) for f in filas]


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
        self.usuarios = RepositorioUsuariosSQL(self._sesion)
        self.socios = RepositorioSociosSQL(self._sesion)
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
            if "uq_usuario_email" in str(exc.orig) or "uq_usuario_documento" in str(exc.orig):
                raise CuentaYaExiste from exc
            raise


def crear_motor(config: Settings) -> AsyncEngine:
    return create_async_engine(config.database_url, pool_size=config.db_pool_size, pool_pre_ping=True)


def fabrica_unidad_de_trabajo(motor: AsyncEngine):
    sesiones = async_sessionmaker(motor, expire_on_commit=False)
    return lambda: UnidadDeTrabajoSQL(sesiones)
