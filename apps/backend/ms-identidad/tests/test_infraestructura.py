from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app import main
from app.config import Settings
from app.dependencies import obtener_uow, obtener_verificador_kyc
from app.domain.modelos import EstadoUsuario, Usuario
from app.infrastructure.kyc import VerificadorKYCStub
from app.infrastructure.sql import (
    UnidadDeTrabajoSQL,
    UsuarioFila,
    crear_motor,
    fabrica_unidad_de_trabajo,
)
from app.ports.persistencia import CuentaYaExiste


class SesionFalsa:
    def __init__(self, error_commit: Exception | None = None, fila=None) -> None:
        self.agregados: list = []
        self.error_commit = error_commit
        self.fila = fila
        self.commits = self.rollbacks = self.cierres = 0

    def add(self, objeto) -> None:
        self.agregados.append(objeto)

    async def scalar(self, _consulta):
        return self.fila

    async def commit(self) -> None:
        self.commits += 1
        if self.error_commit is not None:
            raise self.error_commit

    async def rollback(self) -> None:
        self.rollbacks += 1

    async def close(self) -> None:
        self.cierres += 1


def _integridad(mensaje: str) -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception(mensaje))


def _usuario() -> Usuario:
    return Usuario.crear(
        tipo_documento="CC",
        numero_documento="1012345678",
        email="camila@correo.com",
        password_plano="clave-secreta-123",
    )


async def test_agregar_usuario_escribe_la_fila_y_confirma():
    sesion = SesionFalsa()
    usuario = _usuario()

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        await tx.usuarios.agregar(usuario)
        await tx.confirmar()

    (fila,) = sesion.agregados
    assert isinstance(fila, UsuarioFila)
    assert (fila.usuario_id, fila.email, fila.tipo_documento, fila.numero_documento) == (
        usuario.id,
        usuario.email,
        usuario.tipo_documento,
        usuario.numero_documento,
    )
    assert fila.password_hash == usuario.password_hash
    assert (sesion.commits, sesion.cierres) == (1, 1)


async def test_obtener_por_email_mapea_la_fila_al_dominio():
    fila = UsuarioFila(
        usuario_id=uuid4(),
        tipo_documento="CC",
        numero_documento="123",
        email="camila@correo.com",
        password_hash="hash",
        estado="ACTIVO",
    )

    async with UnidadDeTrabajoSQL(lambda: SesionFalsa(fila=fila)) as tx:
        usuario = await tx.usuarios.obtener_por_email("camila@correo.com")

    assert usuario.id == fila.usuario_id
    assert usuario.estado is EstadoUsuario.ACTIVO


async def test_obtener_por_email_sin_fila_devuelve_none():
    async with UnidadDeTrabajoSQL(lambda: SesionFalsa()) as tx:
        assert await tx.usuarios.obtener_por_email("nadie@correo.com") is None


async def test_obtener_por_documento_sin_fila_devuelve_none():
    async with UnidadDeTrabajoSQL(lambda: SesionFalsa()) as tx:
        assert await tx.usuarios.obtener_por_documento("CC", "123") is None


async def test_email_duplicado_se_traduce_al_puerto():
    sesion = SesionFalsa(error_commit=_integridad('duplicate key "uq_usuario_email"'))

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        with pytest.raises(CuentaYaExiste):
            await tx.confirmar()

    # Un rollback dentro de confirmar() (al traducir el IntegrityError) y otro
    # al salir del context manager (__aexit__ siempre hace rollback).
    assert sesion.rollbacks == 2


async def test_documento_duplicado_se_traduce_al_puerto():
    sesion = SesionFalsa(error_commit=_integridad('duplicate key "uq_usuario_documento"'))

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        with pytest.raises(CuentaYaExiste):
            await tx.confirmar()


async def test_otra_violacion_de_integridad_se_propaga():
    sesion = SesionFalsa(error_commit=_integridad("violates check constraint"))

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        with pytest.raises(IntegrityError):
            await tx.confirmar()


async def test_motor_y_fabrica_no_abren_conexion_al_crearse():
    motor = crear_motor(Settings(database_url="postgresql+asyncpg://u:p@localhost:5432/db", db_pool_size=3))
    try:
        assert motor.pool.size() == 3
        assert isinstance(fabrica_unidad_de_trabajo(motor)(), UnidadDeTrabajoSQL)
    finally:
        await motor.dispose()


def test_al_arrancar_la_app_crea_la_fabrica_y_libera_el_motor(monkeypatch):
    motor = SimpleNamespace(liberado=False)

    async def liberar():
        motor.liberado = True

    motor.dispose = liberar
    monkeypatch.setattr(main, "crear_motor", lambda _config: motor)

    app = main.crear_app()
    with TestClient(app) as cliente:
        assert app.state.fabrica_uow is not None
        assert isinstance(app.state.verificador_kyc, VerificadorKYCStub)
        assert cliente.get("/health/live").json() == {"status": "ok"}
        assert cliente.get("/metrics").status_code == 200
    assert motor.liberado


def test_al_arrancar_la_app_configura_el_doble_de_kyc_desde_el_entorno(monkeypatch):
    motor = SimpleNamespace()

    async def liberar():
        pass

    motor.dispose = liberar
    monkeypatch.setattr(main, "crear_motor", lambda _config: motor)
    monkeypatch.setenv("DOBLE_KYC_LATENCIA_MS", "500")
    monkeypatch.setenv("DOBLE_KYC_FALLAR", "true")

    app = main.crear_app()
    with TestClient(app):
        assert (app.state.verificador_kyc._latencia_ms, app.state.verificador_kyc._fallar) == (500, True)


def test_dependencias_leen_el_estado_de_la_app():
    estado = SimpleNamespace(fabrica_uow=object(), verificador_kyc=object())
    request = SimpleNamespace(app=SimpleNamespace(state=estado))

    assert obtener_uow(request) is estado.fabrica_uow
    assert obtener_verificador_kyc(request) is estado.verificador_kyc
