from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app import main
from app.config import Settings
from app.dependencies import obtener_pasarela, obtener_suscripciones, obtener_uow
from app.domain.errores import DependenciaNoDisponible
from app.domain.modelos import (
    EstadoPago,
    Pago,
    ResultadoPasarela,
    pago_prima_registrado,
)
from app.infrastructure.externos import PasarelaStub, SuscripcionesHTTP
from app.infrastructure.sql import (
    MedioPagoFila,
    OutboxFila,
    PagoFila,
    TransaccionFila,
    UnidadDeTrabajoSQL,
    crear_motor,
    fabrica_unidad_de_trabajo,
)
from app.ports.persistencia import ClaveIdempotenciaDuplicada


class _Resultado:
    def __init__(self, fila) -> None:
        self._fila = fila

    def first(self):
        return self._fila


class SesionFalsa:
    def __init__(self, error_commit: Exception | None = None, fila=None) -> None:
        self.agregados: list = []
        self.error_commit = error_commit
        self.fila = fila
        self.commits = self.rollbacks = self.cierres = 0

    def add(self, objeto) -> None:
        self.agregados.append(objeto)

    async def execute(self, _consulta):
        return _Resultado(self.fila)

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


def _pago() -> Pago:
    return Pago.registrar_prima(
        uuid4(), uuid4(), Decimal("100.00"), ResultadoPasarela(EstadoPago.APROBADO, "stub", "stub-1")
    )


async def test_agregar_pago_escribe_medio_pago_transaccion_y_evento():
    sesion = SesionFalsa()
    pago = _pago()

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        await tx.pagos.agregar(pago, "tok_visa")
        await tx.outbox.agregar(pago_prima_registrado(pago))
        await tx.confirmar()

    medio, fila, transaccion, evento = sesion.agregados
    assert isinstance(medio, MedioPagoFila)
    assert (medio.usuario_id, medio.token_referencia) == (pago.usuario_id, "tok_visa")
    assert isinstance(fila, PagoFila)
    assert (fila.pago_id, fila.oferta_id, fila.prima_id, fila.concepto, fila.estado) == (
        pago.id,
        pago.oferta_id,
        None,
        "PRIMA",
        "APROBADO",
    )
    assert fila.medio_pago_id == medio.medio_pago_id
    assert isinstance(transaccion, TransaccionFila)
    assert (transaccion.pago_id, transaccion.idempotency_key) == (pago.id, pago.idempotency_key)
    assert isinstance(evento, OutboxFila) and evento.tipo == "PagoPrimaRegistrado"
    assert (sesion.commits, sesion.cierres) == (1, 1)


async def test_obtener_mapea_pago_transaccion_y_medio_al_dominio():
    pago_id, oferta_id, usuario_id = uuid4(), uuid4(), uuid4()
    fila = (
        PagoFila(
            pago_id=pago_id,
            medio_pago_id=uuid4(),
            oferta_id=oferta_id,
            monto=Decimal("10.00"),
            concepto="PRIMA",
            estado="RECHAZADO",
            fecha=datetime.now(UTC),
        ),
        TransaccionFila(
            transaccion_id=uuid4(),
            pago_id=pago_id,
            proveedor="stub",
            referencia_externa=None,
            estado="RECHAZADO",
            idempotency_key=f"cobro-prima:{oferta_id}",
        ),
        MedioPagoFila(medio_pago_id=uuid4(), usuario_id=usuario_id, tipo="TOKEN", token_referencia="t"),
    )

    async with UnidadDeTrabajoSQL(lambda: SesionFalsa(fila=fila)) as tx:
        por_id = await tx.pagos.obtener(pago_id)
        por_clave = await tx.pagos.obtener_por_clave(f"cobro-prima:{oferta_id}")

    assert por_id == por_clave
    assert (por_id.id, por_id.oferta_id, por_id.usuario_id) == (pago_id, oferta_id, usuario_id)
    assert por_id.estado is EstadoPago.RECHAZADO
    assert por_id.referencia_externa == ""


async def test_obtener_sin_fila_devuelve_none():
    async with UnidadDeTrabajoSQL(lambda: SesionFalsa()) as tx:
        assert await tx.pagos.obtener(uuid4()) is None
        assert await tx.pagos.obtener_por_clave("cobro-prima:x") is None


async def test_clave_duplicada_se_traduce_al_puerto():
    sesion = SesionFalsa(error_commit=_integridad('duplicate key "uq_transaccion_idempotency"'))

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        with pytest.raises(ClaveIdempotenciaDuplicada):
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


def _suscripciones(manejador) -> SuscripcionesHTTP:
    return SuscripcionesHTTP(httpx.AsyncClient(base_url="http://ms-suscripcion", transport=httpx.MockTransport(manejador)))


@pytest.mark.parametrize(("decision", "esperado"), [("ACEPTADA", True), ("RECHAZADA", False)])
async def test_suscripcion_http_lee_la_decision(decision, esperado):
    solicitud_id = uuid4()
    rutas = []

    def manejador(request):
        rutas.append(request.url.path)
        return httpx.Response(200, json={"decision": decision})

    assert await _suscripciones(manejador).aceptada(solicitud_id) is esperado
    assert rutas == [f"/v1/suscripciones/{solicitud_id}"]


async def test_suscripcion_inexistente_no_esta_aceptada():
    assert await _suscripciones(lambda _r: httpx.Response(404)).aceptada(uuid4()) is False


async def test_suscripcion_con_error_del_servicio_no_esta_disponible():
    with pytest.raises(DependenciaNoDisponible):
        await _suscripciones(lambda _r: httpx.Response(500)).aceptada(uuid4())


async def test_suscripcion_sin_red_no_esta_disponible():
    def manejador(request):
        raise httpx.ConnectError("sin red", request=request)

    with pytest.raises(DependenciaNoDisponible):
        await _suscripciones(manejador).aceptada(uuid4())


def test_dependencia_caida_responde_503(client, suscripciones):
    async def caida(_solicitud_id):
        raise DependenciaNoDisponible("ms-suscripcion")

    suscripciones.aceptada = caida
    cuerpo = {
        "solicitud_id": str(uuid4()),
        "oferta_id": str(uuid4()),
        "usuario_id": str(uuid4()),
        "monto": "10.00",
        "token_medio_pago": "tok_visa",
    }

    respuesta = client.post("/v1/pagos/primas", json=cuerpo)

    assert respuesta.status_code == 503
    assert respuesta.json()["codigo"] == "dependencia_no_disponible"


def test_al_arrancar_la_app_crea_adaptadores_y_libera_recursos(monkeypatch):
    motor = SimpleNamespace(liberado=False)

    async def liberar():
        motor.liberado = True

    motor.dispose = liberar
    monkeypatch.setattr(main, "crear_motor", lambda _config: motor)

    app = main.crear_app()
    with TestClient(app) as cliente:
        assert app.state.fabrica_uow is not None
        assert isinstance(app.state.suscripciones, SuscripcionesHTTP)
        assert isinstance(app.state.pasarela, PasarelaStub)
        assert cliente.get("/health/live").json() == {"status": "ok"}
        assert cliente.get("/metrics").status_code == 200
    assert motor.liberado


def test_dependencias_leen_el_estado_de_la_app():
    estado = SimpleNamespace(fabrica_uow=object(), suscripciones=object(), pasarela=object())
    request = SimpleNamespace(app=SimpleNamespace(state=estado))

    assert obtener_uow(request) is estado.fabrica_uow
    assert obtener_suscripciones(request) is estado.suscripciones
    assert obtener_pasarela(request) is estado.pasarela
