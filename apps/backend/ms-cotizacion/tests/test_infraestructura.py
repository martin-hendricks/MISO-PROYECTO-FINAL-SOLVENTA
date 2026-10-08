from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app import main
from app.config import Settings
from app.dependencies import obtener_catalogo, obtener_uow
from app.domain.errores import ErrorDominio, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import EventoDominio
from app.infrastructure import catalogo_sql
from app.infrastructure.catalogo_sql import CatalogoSQL, ProductoFila
from app.infrastructure.sql import OutboxFila, UnidadDeTrabajoSQL, crear_motor, fabrica_unidad_de_trabajo
from app.ports.persistencia import ClaveIdempotenciaDuplicada

from .dobles import CatalogoEnMemoria


class SesionFalsa:
    def __init__(self, error_commit: Exception | None = None, filas=()) -> None:
        self.agregados: list = []
        self.error_commit = error_commit
        self.filas = list(filas)
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

    async def scalars(self, _consulta):
        return iter(self.filas)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc) -> None:
        await self.close()


def _integridad(mensaje: str) -> IntegrityError:
    return IntegrityError("INSERT", {}, Exception(mensaje))


async def test_la_unidad_de_trabajo_escribe_el_evento_en_el_outbox_y_confirma():
    sesion = SesionFalsa()
    evento = EventoDominio(tipo="ProductoConsultado", agregado_id=uuid4(), payload={"producto": "soat-motocicleta"})

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        await tx.outbox.agregar(evento)
        await tx.confirmar()

    [fila] = sesion.agregados
    assert isinstance(fila, OutboxFila)
    assert (fila.id, fila.tipo, fila.payload) == (evento.id, evento.tipo, evento.payload)
    assert (sesion.commits, sesion.cierres) == (1, 1)


async def test_clave_de_idempotencia_duplicada_se_traduce_al_puerto():
    sesion = SesionFalsa(error_commit=_integridad('duplicate key "uq_solicitud_idempotency_key"'))

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


async def test_cargar_lee_los_productos_de_la_bd(monkeypatch):
    fila = ProductoFila(codigo="soat-motocicleta", nombre="SOAT", ramo="soat", moneda="COP", coberturas=[], datos_riesgo=[])
    monkeypatch.setattr(catalogo_sql, "AsyncSession", lambda _motor: SesionFalsa(filas=[fila]))

    catalogo = await CatalogoSQL.cargar(motor=None)

    assert catalogo.obtener("soat-motocicleta").moneda == "COP"


async def test_catalogo_vacio_impide_arrancar(monkeypatch):
    monkeypatch.setattr(catalogo_sql, "AsyncSession", lambda _motor: SesionFalsa())

    with pytest.raises(RuntimeError, match="vacío"):
        await CatalogoSQL.cargar(motor=None)


def test_al_arrancar_la_app_carga_el_catalogo_y_libera_el_motor(monkeypatch):
    motor = SimpleNamespace(liberado=False)

    async def liberar():
        motor.liberado = True

    motor.dispose = liberar
    catalogo = CatalogoEnMemoria()

    async def cargar(_motor):
        return catalogo

    monkeypatch.setattr(main, "crear_motor", lambda _config: motor)
    monkeypatch.setattr(main.CatalogoSQL, "cargar", cargar)

    app = main.crear_app()
    with TestClient(app):
        assert app.state.catalogo is catalogo
        assert app.state.fabrica_uow is not None
    assert motor.liberado


@pytest.mark.parametrize(
    ("error", "estado"),
    [
        (ReglaDeNegocioViolada("regla", "violada"), 422),
        (TransicionInvalida("a", "b"), 409),
        (ErrorDominio("genérico"), 400),
    ],
)
def test_mapeo_de_errores_de_dominio_a_http(error, estado):
    assert main.estado_http(error) == estado


def test_error_de_dominio_responde_con_codigo_y_mensaje(client):
    app = client.app

    @app.get("/prueba-error")
    async def lanzar():
        raise TransicionInvalida("a", "b")

    respuesta = client.get("/prueba-error")

    assert respuesta.status_code == 409
    assert respuesta.json() == {"codigo": "transicion_invalida", "mensaje": "No se puede pasar de 'a' a 'b'"}


def test_dependencias_leen_el_estado_de_la_app():
    estado = SimpleNamespace(fabrica_uow=object(), catalogo=CatalogoEnMemoria())
    request = SimpleNamespace(app=SimpleNamespace(state=estado))

    assert obtener_uow(request) is estado.fabrica_uow
    assert obtener_catalogo(request) is estado.catalogo
