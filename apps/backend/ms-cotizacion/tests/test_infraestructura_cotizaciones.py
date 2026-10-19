import json
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from decimal import Decimal

from app.dependencies import obtener_adaptador_perfil_riesgo, obtener_config
from app.domain.modelos import EstadoSolicitud, SolicitudCotizacion
from app.domain.oferta import Oferta
from app.domain.riesgo import OrigenFactorRiesgo
from app.infrastructure.sql import (
    OfertaFila,
    ReglaRatingFila,
    RepositorioOfertasSQL,
    RepositorioReglasRatingSQL,
    RepositorioSolicitudesSQL,
    SolicitudFila,
)


class SesionFalsa:
    def __init__(self, filas=()) -> None:
        self.agregados: list = []
        self.flushes = 0
        self._filas = list(filas)

    def add(self, objeto) -> None:
        self.agregados.append(objeto)

    async def flush(self) -> None:
        self.flushes += 1

    async def get(self, modelo, id_):
        pk = modelo.__mapper__.primary_key[0].name
        return next((f for f in self._filas if getattr(f, pk) == id_), None)

    async def scalar(self, _consulta):
        return self._filas[0] if self._filas else None


def _solicitud() -> SolicitudCotizacion:
    return SolicitudCotizacion(
        id=uuid4(),
        idempotency_key="clave-0001",
        usuario_id=uuid4(),
        socio_id=uuid4(),
        consentimiento_id=uuid4(),
        producto="soat-motocicleta",
        canal="app-socio",
        datos_riesgo={"cilindraje_cc": 150},
        estado=EstadoSolicitud.RECIBIDA,
        creada_en=datetime.now(UTC),
    )


async def test_agregar_persiste_la_fila_y_hace_flush_inmediato():
    sesion = SesionFalsa()
    repo = RepositorioSolicitudesSQL(sesion)
    solicitud = _solicitud()

    await repo.agregar(solicitud)

    [fila] = sesion.agregados
    assert isinstance(fila, SolicitudFila)
    assert (fila.solicitud_id, fila.idempotency_key) == (solicitud.id, solicitud.idempotency_key)
    assert sesion.flushes == 1


async def test_obtener_inexistente_devuelve_none():
    repo = RepositorioSolicitudesSQL(SesionFalsa())

    assert await repo.obtener(uuid4()) is None


async def test_obtener_por_clave_sin_coincidencia_devuelve_none():
    repo = RepositorioSolicitudesSQL(SesionFalsa())

    assert await repo.obtener_por_clave("clave-inexistente") is None


async def test_actualizar_cambia_el_estado_de_la_fila():
    fila = SolicitudFila(
        solicitud_id=uuid4(),
        idempotency_key="clave-0001",
        usuario_id=uuid4(),
        socio_id=uuid4(),
        consentimiento_id=uuid4(),
        producto="soat-motocicleta",
        canal="app-socio",
        datos_riesgo={},
        estado=EstadoSolicitud.RECIBIDA.value,
        creada_en=datetime.now(UTC),
    )
    sesion = SesionFalsa(filas=[fila])
    repo = RepositorioSolicitudesSQL(sesion)
    solicitud = _solicitud()
    solicitud.id = fila.solicitud_id
    solicitud.estado = EstadoSolicitud.COTIZADA

    await repo.actualizar(solicitud)

    assert fila.estado == EstadoSolicitud.COTIZADA.value


async def test_obtener_vigente_devuelve_la_regla_deserializada():
    formula = {"insumos_requeridos": ["cilindraje_cc"], "base": "120000", "gastos_fijos": "8500", "moneda": "COP"}
    fila = ReglaRatingFila(regla_id=uuid4(), producto="soat-motocicleta", version="0001", formula=json.dumps(formula))
    repo = RepositorioReglasRatingSQL(SesionFalsa(filas=[fila]))

    regla = await repo.obtener_vigente("soat-motocicleta")

    assert (regla.id, regla.producto, regla.version, regla.formula) == (fila.regla_id, "soat-motocicleta", "0001", formula)


async def test_obtener_vigente_sin_regla_configurada_devuelve_none():
    repo = RepositorioReglasRatingSQL(SesionFalsa())

    assert await repo.obtener_vigente("producto-sin-regla") is None


def test_obtener_adaptador_perfil_riesgo_lee_el_estado_de_la_app():
    estado = SimpleNamespace(adaptador_perfil_riesgo=object())
    request = SimpleNamespace(app=SimpleNamespace(state=estado))

    assert obtener_adaptador_perfil_riesgo(request) is estado.adaptador_perfil_riesgo


def test_obtener_config_lee_el_estado_de_la_app():
    estado = SimpleNamespace(config=object())
    request = SimpleNamespace(app=SimpleNamespace(state=estado))

    assert obtener_config(request) is estado.config


def _oferta() -> Oferta:
    return Oferta(
        id=uuid4(),
        solicitud_id=uuid4(),
        regla_id=uuid4(),
        version_regla="0001",
        prima_neta=Decimal("120000.00"),
        gastos_expedicion=Decimal("8500.00"),
        moneda="COP",
        coberturas=["muerte", "incapacidad_permanente"],
        factor_riesgo=Decimal("1.1000"),
        factor_riesgo_origen=OrigenFactorRiesgo.REAL,
        vence_en=datetime.now(UTC),
    )


async def test_ofertas_agregar_persiste_la_fila():
    sesion = SesionFalsa()
    repo = RepositorioOfertasSQL(sesion)
    oferta = _oferta()

    await repo.agregar(oferta)

    [fila] = sesion.agregados
    assert isinstance(fila, OfertaFila)
    assert (fila.oferta_id, fila.solicitud_id) == (oferta.id, oferta.solicitud_id)


async def test_ofertas_obtener_inexistente_devuelve_none():
    repo = RepositorioOfertasSQL(SesionFalsa())

    assert await repo.obtener(uuid4()) is None


async def test_ofertas_obtener_por_solicitud_sin_coincidencia_devuelve_none():
    repo = RepositorioOfertasSQL(SesionFalsa())

    assert await repo.obtener_por_solicitud(uuid4()) is None


async def test_ofertas_obtener_devuelve_la_oferta_reconstruida():
    oferta = _oferta()
    fila = OfertaFila(
        oferta_id=oferta.id,
        solicitud_id=oferta.solicitud_id,
        regla_id=oferta.regla_id,
        version_regla=oferta.version_regla,
        prima=oferta.prima,
        prima_neta=oferta.prima_neta,
        gastos_expedicion=oferta.gastos_expedicion,
        moneda=oferta.moneda,
        coberturas=",".join(oferta.coberturas),
        factor_riesgo=oferta.factor_riesgo,
        factor_riesgo_origen=oferta.factor_riesgo_origen.value,
        vence_en=oferta.vence_en,
    )
    repo = RepositorioOfertasSQL(SesionFalsa(filas=[fila]))

    reconstruida = await repo.obtener_por_solicitud(oferta.solicitud_id)

    assert (reconstruida.id, reconstruida.solicitud_id) == (oferta.id, oferta.solicitud_id)
