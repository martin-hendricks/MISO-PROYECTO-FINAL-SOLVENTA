from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import DateTime

from app.domain.modelos import Siniestro, SnapshotPoliza
from app.infrastructure.sql import Base, RepositorioSiniestrosSQL, SiniestroFila, _copiar_a_fila


def test_todas_las_fechas_se_mapean_como_timestamptz():
    columnas = [
        f"{tabla.name}.{columna.name}"
        for tabla in Base.metadata.tables.values()
        for columna in tabla.columns
        if isinstance(columna.type, DateTime) and not columna.type.timezone
    ]
    assert columnas == []


def test_tablas_esperadas_estan_registradas():
    nombres = {tabla.name for tabla in Base.metadata.tables.values()}
    assert nombres == {
        "siniestro",
        "siniestro_transicion",
        "evento_parametrico",
        "evaluacion_umbral",
        "pago_parametrico",
        "outbox_evento",
        # HU-157: siniestro asistido
        "parametro_ramo",
        "siniestro_adjunto",
        "siniestro_decision",
        "pago_siniestro",
        "pago_siniestro_intento",
    }


def test_claves_de_idempotencia_son_unicas():
    tablas = {t.name: t for t in Base.metadata.tables.values()}
    assert tablas["siniestro"].c.evento_id.unique
    assert tablas["evento_parametrico"].c.evento_id.primary_key
    assert tablas["evaluacion_umbral"].c.evento_id.unique
    assert tablas["pago_parametrico"].c.evento_id.unique


class _Sesion:
    def __init__(self, filas: list) -> None:
        self.filas = filas
        self.lecturas = 0

    async def scalars(self, _consulta):
        self.lecturas += 1
        return self.filas if self.lecturas == 1 else []

    async def get(self, _modelo, _identificador):
        return self.filas[0] if self.filas else None


async def test_listar_filtra_por_usuario_y_sin_filtro_recorre_la_tabla():
    usuario_id = uuid4()
    fila = SiniestroFila(
        id=uuid4(),
        evento_id="evt-lista",
        estado="recibido",
        creado_en=datetime.now(UTC),
        poliza_id=None,
        usuario_id=usuario_id,
    )
    repo = RepositorioSiniestrosSQL(_Sesion([fila]))
    encontrados = await repo.listar(10, usuario_id)
    assert [siniestro.evento_id for siniestro in encontrados] == ["evt-lista"]

    vacio = RepositorioSiniestrosSQL(_Sesion([]))
    assert await vacio.listar(10) == []


def test_copiar_a_fila_guarda_el_lugar():
    siniestro = Siniestro.avisar(
        usuario_id=uuid4(),
        poliza=SnapshotPoliza(
            poliza_id=uuid4(),
            numero="POL-1",
            ramo="soat",
            estado="vigente",
            inicio_vigencia=date.today() - timedelta(days=10),
            fin_vigencia=date.today() + timedelta(days=10),
            suma_asegurada=Decimal("1000"),
        ),
        fecha_hecho=date.today() - timedelta(days=1),
        descripcion="Choque",
        lugar="Calle 72",
        canal="movil",
    )
    fila = SiniestroFila(id=siniestro.id, creado_en=siniestro.creado_en, estado="recibido")
    _copiar_a_fila(siniestro, fila)
    assert fila.lugar == "Calle 72"


def test_siniestro_tiene_poliza_id_opcional():
    tablas = {t.name: t for t in Base.metadata.tables.values()}
    columna = tablas["siniestro"].c.poliza_id
    assert columna.nullable
