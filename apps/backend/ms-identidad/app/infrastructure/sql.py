from __future__ import annotations

from uuid import UUID

from sqlalchemy import MetaData, String, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import Settings
from app.domain.modelos import EstadoUsuario, Usuario
from app.ports.persistencia import CuentaYaExiste

ESQUEMA = "ms_identidad"


class Base(DeclarativeBase):
    metadata = MetaData(schema=ESQUEMA)


class UsuarioFila(Base):
    __tablename__ = "usuario"

    usuario_id: Mapped[UUID] = mapped_column(primary_key=True)
    tipo_documento: Mapped[str] = mapped_column(String)
    numero_documento: Mapped[str] = mapped_column(String)
    email: Mapped[str] = mapped_column(String)
    password_hash: Mapped[str] = mapped_column(String)
    estado: Mapped[str] = mapped_column(String)


def _a_dominio(fila: UsuarioFila) -> Usuario:
    return Usuario(
        id=fila.usuario_id,
        tipo_documento=fila.tipo_documento,
        numero_documento=fila.numero_documento,
        email=fila.email,
        password_hash=fila.password_hash,
        estado=EstadoUsuario(fila.estado),
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

    async def agregar(self, usuario: Usuario) -> None:
        self._s.add(
            UsuarioFila(
                usuario_id=usuario.id,
                tipo_documento=usuario.tipo_documento,
                numero_documento=usuario.numero_documento,
                email=usuario.email,
                password_hash=usuario.password_hash,
                estado=usuario.estado.value,
            )
        )


class UnidadDeTrabajoSQL:
    def __init__(self, fabrica: async_sessionmaker[AsyncSession]) -> None:
        self._fabrica = fabrica

    async def __aenter__(self) -> UnidadDeTrabajoSQL:
        self._sesion = self._fabrica()
        self.usuarios = RepositorioUsuariosSQL(self._sesion)
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
