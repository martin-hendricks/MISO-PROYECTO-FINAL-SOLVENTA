from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app import main
from app.application import casos_uso
from app.config import Settings
from app.dependencies import obtener_uow
from app.domain.modelos import Decision, Suscripcion, suscripcion_decidida
from app.infrastructure.sql import (
    OutboxFila,
    ReglaFila,
    SuscripcionFila,
    UnidadDeTrabajoSQL,
    crear_motor,
    fabrica_unidad_de_trabajo,
)
from app.ports.persistencia import SolicitudYaDecidida

from .dobles import regla


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


def _suscripcion() -> Suscripcion:
    return Suscripcion.decidir(uuid4(), uuid4(), Decimal("0.9"), regla())


async def test_agregar_suscripcion_y_evento_escribe_ambas_filas_y_confirma():
    sesion = SesionFalsa()
    suscripcion = _suscripcion()

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        await tx.suscripciones.agregar(suscripcion)
        await tx.outbox.agregar(suscripcion_decidida(suscripcion))
        await tx.confirmar()

    fila, evento = sesion.agregados
    assert isinstance(fila, SuscripcionFila)
    assert (fila.suscripcion_id, fila.solicitud_id, fila.decision, fila.motivo) == (
        suscripcion.id,
        suscripcion.solicitud_id,
        "RECHAZADA",
        "Riesgo fuera del apetito",
    )
    assert isinstance(evento, OutboxFila)
    assert evento.tipo == "SuscripcionDecidida"
    assert (sesion.commits, sesion.cierres) == (1, 1)


async def test_obtener_por_solicitud_mapea_la_fila_al_dominio():
    fila = SuscripcionFila(
        suscripcion_id=uuid4(),
        solicitud_id=uuid4(),
        perfil_id=uuid4(),
        decision="ACEPTADA",
        motivo=None,
        evaluada_en=datetime.now(UTC),
    )

    async with UnidadDeTrabajoSQL(lambda: SesionFalsa(fila=fila)) as tx:
        suscripcion = await tx.suscripciones.obtener_por_solicitud(fila.solicitud_id)

    assert suscripcion.id == fila.suscripcion_id
    assert suscripcion.decision is Decision.ACEPTADA
    assert suscripcion.motivo == ""


async def test_obtener_por_solicitud_sin_fila_devuelve_none():
    async with UnidadDeTrabajoSQL(lambda: SesionFalsa()) as tx:
        assert await tx.suscripciones.obtener_por_solicitud(uuid4()) is None


async def test_regla_vigente_se_lee_de_la_tabla():
    fila = ReglaFila(
        regla_id=uuid4(),
        score_maximo=Decimal("0.6"),
        motivo_aceptacion="dentro",
        motivo_rechazo="fuera",
        vigente=True,
    )

    async with UnidadDeTrabajoSQL(lambda: SesionFalsa(fila=fila)) as tx:
        vigente = await tx.reglas.vigente()

    assert (vigente.id, vigente.score_maximo, vigente.motivo_rechazo) == (fila.regla_id, Decimal("0.6"), "fuera")


async def test_sin_regla_vigente_devuelve_none():
    async with UnidadDeTrabajoSQL(lambda: SesionFalsa()) as tx:
        assert await tx.reglas.vigente() is None


async def test_solicitud_duplicada_se_traduce_al_puerto():
    sesion = SesionFalsa(error_commit=_integridad('duplicate key "uq_suscripcion_solicitud"'))

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        with pytest.raises(SolicitudYaDecidida):
            await tx.confirmar()

    assert sesion.rollbacks == 2


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


async def test_duplicada_sin_ganadora_visible_falla(uow, almacen):
    almacen.chocar_en_proximo_commit = _suscripcion()

    with pytest.raises(RuntimeError, match="sin decisión visible"):
        await casos_uso.evaluar_suscripcion(uow, uuid4(), uuid4(), Decimal("0.1"))


def test_al_arrancar_la_app_crea_la_fabrica_y_libera_el_motor(monkeypatch):
    motor = SimpleNamespace(liberado=False)

    async def liberar():
        motor.liberado = True

    motor.dispose = liberar
    monkeypatch.setattr(main, "crear_motor", lambda _config: motor)

    app = main.crear_app()
    with TestClient(app) as cliente:
        assert app.state.fabrica_uow is not None
        assert cliente.get("/health").json() == {"status": "ok"}
        assert cliente.get("/metrics").status_code == 200
    assert motor.liberado


def test_dependencias_leen_el_estado_de_la_app():
    estado = SimpleNamespace(fabrica_uow=object())
    request = SimpleNamespace(app=SimpleNamespace(state=estado))

    assert obtener_uow(request) is estado.fabrica_uow
