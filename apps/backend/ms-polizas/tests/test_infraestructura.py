from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app import main
from app.config import Settings
from app.dependencies import obtener_cobros, obtener_suscripciones, obtener_uow
from app.domain.errores import DependenciaNoDisponible
from app.domain.modelos import Poliza, poliza_emitida
from app.infrastructure.precondiciones import CobrosHTTP, SuscripcionesHTTP
from app.infrastructure.sql import (
    CoberturaFila,
    OutboxFila,
    PolizaFila,
    UnidadDeTrabajoSQL,
    crear_motor,
    fabrica_unidad_de_trabajo,
)
from app.ports.persistencia import PolizaYaEmitida

from .dobles import coberturas


class SesionFalsa:
    def __init__(self, error_commit: Exception | None = None, fila=None, coberturas=(), secuencia=7) -> None:
        self.agregados: list = []
        self.eliminados: list = []
        self.error_commit = error_commit
        self.fila = fila
        self.coberturas = list(coberturas)
        self.secuencia = secuencia
        self.commits = self.rollbacks = self.cierres = 0

    def add(self, objeto) -> None:
        self.agregados.append(objeto)

    async def delete(self, objeto) -> None:
        self.eliminados.append(objeto)

    async def get(self, _tipo, _id):
        return self.fila

    async def scalar(self, consulta):
        if "poliza_numero_seq" in str(consulta):
            return self.secuencia
        return self.fila

    async def scalars(self, _consulta):
        return iter(self.coberturas)

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


def _poliza() -> Poliza:
    return Poliza.emitir(uuid4(), uuid4(), "POL-2026-00000007", coberturas(), date(2026, 10, 23))


async def test_agregar_poliza_escribe_poliza_coberturas_y_evento_y_confirma():
    sesion = SesionFalsa()
    poliza = _poliza()

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        await tx.polizas.agregar(poliza)
        await tx.outbox.agregar(poliza_emitida(poliza))
        await tx.confirmar()

    fila, *filas_cobertura, evento = sesion.agregados
    assert isinstance(fila, PolizaFila)
    assert (fila.poliza_id, fila.oferta_id, fila.numero, fila.estado) == (
        poliza.id,
        poliza.oferta_id,
        "POL-2026-00000007",
        "VIGENTE",
    )
    assert all(isinstance(c, CoberturaFila) and c.poliza_id == poliza.id for c in filas_cobertura)
    assert len(filas_cobertura) == 2
    assert isinstance(evento, OutboxFila) and evento.tipo == "PolizaEmitida"
    assert (sesion.commits, sesion.cierres) == (1, 1)


async def test_siguiente_secuencia_usa_la_secuencia_de_la_bd():
    async with UnidadDeTrabajoSQL(lambda: SesionFalsa(secuencia=41)) as tx:
        assert await tx.polizas.siguiente_secuencia() == 41


async def test_obtener_mapea_la_fila_y_sus_coberturas_al_dominio():
    fila = PolizaFila(
        poliza_id=uuid4(),
        oferta_id=uuid4(),
        usuario_id=uuid4(),
        numero="POL-2026-00000001",
        inicio_vigencia=date(2026, 1, 1),
        fin_vigencia=date(2026, 12, 31),
        estado="VIGENTE",
    )
    cobertura = CoberturaFila(
        cobertura_id=uuid4(), poliza_id=fila.poliza_id, nombre="RC", suma_asegurada=Decimal("10"), deducible=Decimal("1")
    )

    async with UnidadDeTrabajoSQL(lambda: SesionFalsa(fila=fila, coberturas=[cobertura])) as tx:
        por_id = await tx.polizas.obtener(fila.poliza_id)
        por_oferta = await tx.polizas.obtener_por_oferta(fila.oferta_id)

    assert por_id == por_oferta
    assert por_id.numero == "POL-2026-00000001"
    assert [(c.nombre, c.suma_asegurada, c.deducible) for c in por_id.coberturas] == [
        ("RC", Decimal("10"), Decimal("1"))
    ]


async def test_obtener_sin_fila_devuelve_none():
    async with UnidadDeTrabajoSQL(lambda: SesionFalsa()) as tx:
        assert await tx.polizas.obtener(uuid4()) is None
        assert await tx.polizas.obtener_por_oferta(uuid4()) is None
        assert await tx.polizas.obtener_por_numero("POL-2026-00000001") is None


async def test_obtener_por_numero_mapea_la_fila_al_dominio():
    fila = PolizaFila(
        poliza_id=uuid4(),
        oferta_id=uuid4(),
        usuario_id=uuid4(),
        numero="POL-2026-00000001",
        inicio_vigencia=date(2026, 1, 1),
        fin_vigencia=date(2026, 12, 31),
        estado="VIGENTE",
    )

    async with UnidadDeTrabajoSQL(lambda: SesionFalsa(fila=fila)) as tx:
        encontrada = await tx.polizas.obtener_por_numero(fila.numero)

    assert encontrada.numero == fila.numero


async def test_listar_por_usuario_usa_limite_y_orden_descendente():
    usuario_id = uuid4()
    fila = PolizaFila(
        poliza_id=uuid4(),
        oferta_id=uuid4(),
        usuario_id=usuario_id,
        numero="POL-2026-00000001",
        inicio_vigencia=date(2026, 1, 1),
        fin_vigencia=date(2026, 12, 31),
        estado="VIGENTE",
    )

    class SesionConLista(SesionFalsa):
        def __init__(self) -> None:
            super().__init__()
            self.consultas: list = []

        async def scalars(self, consulta):
            self.consultas.append(consulta)
            if len(self.consultas) == 1:
                return iter([fila])
            return iter(self.coberturas)

    sesion = SesionConLista()
    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        resultado = await tx.polizas.listar_por_usuario(usuario_id, limite=5)

    assert [p.numero for p in resultado] == [fila.numero]
    consulta_listado = str(sesion.consultas[0])
    assert "ORDER BY" in consulta_listado and "poliza.inicio_vigencia DESC" in consulta_listado
    assert "LIMIT" in consulta_listado


async def test_actualizar_escribe_los_campos_mutables_y_reemplaza_coberturas():
    poliza = _poliza()
    poliza.cancelar("El cliente lo pidió", date(2026, 11, 1))
    fila = PolizaFila(
        poliza_id=poliza.id,
        oferta_id=poliza.oferta_id,
        usuario_id=poliza.usuario_id,
        numero=poliza.numero,
        inicio_vigencia=poliza.inicio_vigencia,
        fin_vigencia=date(2026, 10, 23),
        estado="VIGENTE",
    )
    cobertura_vieja = CoberturaFila(
        cobertura_id=uuid4(), poliza_id=poliza.id, nombre="vieja", suma_asegurada=Decimal("1"), deducible=Decimal("0")
    )
    sesion = SesionFalsa(fila=fila, coberturas=[cobertura_vieja])

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        await tx.polizas.actualizar(poliza)
        await tx.confirmar()

    assert sesion.eliminados == [cobertura_vieja]
    assert fila.estado == "CANCELADA"
    assert fila.motivo_cancelacion == "El cliente lo pidió"
    assert fila.cancelada_en == date(2026, 11, 1)
    assert [c.poliza_id for c in sesion.agregados if isinstance(c, CoberturaFila)] == [poliza.id] * len(
        poliza.coberturas
    )


async def test_actualizar_sin_fila_existente_falla():
    async with UnidadDeTrabajoSQL(lambda: SesionFalsa(fila=None)) as tx:
        with pytest.raises(ValueError):
            await tx.polizas.actualizar(_poliza())


async def test_oferta_duplicada_se_traduce_al_puerto():
    sesion = SesionFalsa(error_commit=_integridad('duplicate key "uq_poliza_oferta"'))

    async with UnidadDeTrabajoSQL(lambda: sesion) as tx:
        with pytest.raises(PolizaYaEmitida):
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


def _cobros(manejador) -> CobrosHTTP:
    return CobrosHTTP(httpx.AsyncClient(base_url="http://ms-pagos", transport=httpx.MockTransport(manejador)))


@pytest.mark.parametrize(
    ("estado", "misma_oferta", "esperado"),
    [("APROBADO", True, True), ("RECHAZADO", True, False), ("APROBADO", False, False)],
)
async def test_cobros_http_exige_cobro_aprobado_de_la_misma_oferta(estado, misma_oferta, esperado):
    oferta_id, token = uuid4(), uuid4()
    rutas = []

    def manejador(request):
        rutas.append(request.url.path)
        return httpx.Response(200, json={"estado": estado, "oferta_id": str(oferta_id if misma_oferta else uuid4())})

    assert await _cobros(manejador).exitoso(oferta_id, token) is esperado
    assert rutas == [f"/v1/pagos/{token}"]


async def test_cobro_inexistente_no_es_exitoso():
    assert await _cobros(lambda _r: httpx.Response(404)).exitoso(uuid4(), uuid4()) is False


async def test_cobros_con_error_del_servicio_no_esta_disponible():
    with pytest.raises(DependenciaNoDisponible):
        await _cobros(lambda _r: httpx.Response(500)).exitoso(uuid4(), uuid4())


async def test_cobros_sin_red_no_esta_disponible():
    def manejador(request):
        raise httpx.ConnectError("sin red", request=request)

    with pytest.raises(DependenciaNoDisponible):
        await _cobros(manejador).exitoso(uuid4(), uuid4())


def test_dependencia_caida_responde_503(client, suscripciones):
    async def caida(_solicitud_id):
        raise DependenciaNoDisponible("ms-suscripcion")

    suscripciones.aceptada = caida
    cuerpo = {
        "solicitud_id": str(uuid4()),
        "oferta_id": str(uuid4()),
        "usuario_id": str(uuid4()),
        "token_pago_confirmado": str(uuid4()),
        "coberturas": [{"nombre": "RC", "suma_asegurada": "10.00"}],
    }

    respuesta = client.post("/v1/polizas", json=cuerpo)

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
        assert isinstance(app.state.cobros, CobrosHTTP)
        assert cliente.get("/health").json() == {"status": "ok"}
        assert cliente.get("/metrics").status_code == 200
    assert motor.liberado


def test_dependencias_leen_el_estado_de_la_app():
    estado = SimpleNamespace(fabrica_uow=object(), suscripciones=object(), cobros=object())
    request = SimpleNamespace(app=SimpleNamespace(state=estado))

    assert obtener_uow(request) is estado.fabrica_uow
    assert obtener_suscripciones(request) is estado.suscripciones
    assert obtener_cobros(request) is estado.cobros
