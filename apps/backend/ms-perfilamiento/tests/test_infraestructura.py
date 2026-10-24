from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app import main
from app.config import Settings
from app.dependencies import obtener_adaptador_open_data, obtener_adaptador_open_finance, obtener_config, obtener_uow
from app.domain.errores import ConsentimientoNoOtorgado, ErrorDominio, NoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import EventoDominio
from app.infrastructure.sql import OutboxFila, UnidadDeTrabajoSQL, crear_motor, fabrica_unidad_de_trabajo
from app.ports.persistencia import ClaveIdempotenciaDuplicada


class SesionFalsa:
    def __init__(self, error_commit: Exception | None = None) -> None:
        self.agregados: list = []
        self.error_commit = error_commit
        self.commits = self.rollbacks = self.cierres = 0

    def add(self, objeto) -> None:
        self.agregados.append(objeto)

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


async def test_la_unidad_de_trabajo_escribe_el_evento_en_el_outbox_y_confirma():
    sesion = SesionFalsa()
    evento = EventoDominio(tipo="OfertaHipotecarioEmitida", agregado_id=uuid4(), payload={"precio": "1000"})

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        await tx.outbox.agregar(evento)
        await tx.confirmar()

    [fila] = sesion.agregados
    assert isinstance(fila, OutboxFila)
    assert (fila.id, fila.tipo, fila.payload) == (evento.id, evento.tipo, evento.payload)
    assert (sesion.commits, sesion.cierres) == (1, 1)


async def test_clave_de_idempotencia_duplicada_se_traduce_al_puerto():
    sesion = SesionFalsa(error_commit=_integridad('duplicate key "uq_oferta_idempotency_key"'))

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        with pytest.raises(ClaveIdempotenciaDuplicada):
            await tx.confirmar()

    assert sesion.rollbacks == 2


async def test_otra_violacion_de_integridad_se_propaga():
    sesion = SesionFalsa(error_commit=_integridad("violates foreign key constraint"))

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


def test_al_arrancar_la_app_crea_los_adaptadores_y_libera_el_motor(monkeypatch):
    motor = SimpleNamespace(liberado=False)

    async def liberar():
        motor.liberado = True

    motor.dispose = liberar
    monkeypatch.setattr(main, "crear_motor", lambda _config: motor)

    app = main.crear_app()
    with TestClient(app):
        assert app.state.fabrica_uow is not None
        assert app.state.adaptador_open_finance is not None
        assert app.state.adaptador_open_data is not None
    assert motor.liberado


@pytest.mark.parametrize(
    ("error", "estado"),
    [
        (NoEncontrado("x"), 404),
        (TransicionInvalida("a", "b"), 409),
        (ReglaDeNegocioViolada("regla", "violada"), 422),
        (ConsentimientoNoOtorgado("cliente-1"), 403),
        (ErrorDominio("generico"), 400),
    ],
)
def test_mapeo_de_errores_de_dominio_a_http(error, estado):
    assert main.ESTADO_HTTP.get(type(error), 400) == estado


def test_error_de_dominio_responde_con_codigo_y_mensaje(client):
    app = client.app

    @app.get("/prueba-error")
    async def lanzar():
        raise ConsentimientoNoOtorgado("cliente-1")

    respuesta = client.get("/prueba-error")

    assert respuesta.status_code == 403
    assert respuesta.json()["codigo"] == "consentimiento_no_otorgado"


def test_dependencias_leen_el_estado_de_la_app():
    estado = SimpleNamespace(
        fabrica_uow=object(), adaptador_open_finance=object(), adaptador_open_data=object(), config=Settings()
    )
    request = SimpleNamespace(app=SimpleNamespace(state=estado))

    assert obtener_uow(request) is estado.fabrica_uow
    assert obtener_adaptador_open_finance(request) is estado.adaptador_open_finance
    assert obtener_adaptador_open_data(request) is estado.adaptador_open_data
    assert obtener_config(request) is estado.config
