import json
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.dependencies import obtener_adaptador_perfil_riesgo
from app.domain.modelos import EstadoSolicitud, SolicitudCotizacion
from app.infrastructure.sql import (
    ReglaRatingFila,
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

    async def get(self, _modelo, _id):
        return next((f for f in self._filas if f.solicitud_id == _id), None)

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
