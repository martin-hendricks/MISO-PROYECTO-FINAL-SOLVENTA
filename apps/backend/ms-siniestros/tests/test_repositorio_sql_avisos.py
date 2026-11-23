"""Integración del siniestro asistido contra PostgreSQL con el DDL 03 aplicado."""

import os
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.application import avisos
from app.config import Settings
from app.domain.aviso import ArchivoEvidencia
from app.domain.modelos import EstadoSiniestro, ResultadoDecision, SnapshotPoliza
from app.infrastructure.evidencias import AlmacenEvidenciasEnMemoria
from app.infrastructure.pagos import AdaptadorDesembolsoStub
from app.infrastructure.sql import ESQUEMA, crear_motor, fabrica_unidad_de_trabajo
from app.ports.persistencia import FiltroSiniestros

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif("DATABASE_URL" not in os.environ, reason="requiere DATABASE_URL"),
]

HOY = date.today()


@pytest.fixture
async def motor():
    m = crear_motor(Settings())
    yield m
    await m.dispose()


@pytest.fixture
def uow(motor):
    return fabrica_unidad_de_trabajo(motor)


async def registrar(uow, ramo="proteccion-dispositivo", poliza_id=None, usuario_id=None):
    detalle, _ = await avisos.registrar_aviso(
        uow,
        AlmacenEvidenciasEnMemoria(),
        usuario_id=usuario_id or uuid4(),
        poliza=SnapshotPoliza(
            poliza_id=poliza_id or uuid4(),
            numero="POL-1",
            ramo=ramo,
            estado="vigente",
            inicio_vigencia=HOY - timedelta(days=30),
            fin_vigencia=HOY + timedelta(days=300),
            suma_asegurada=Decimal("5000000"),
        ),
        fecha_hecho=HOY - timedelta(days=1),
        descripcion="Pantalla rota",
        canal="web",
        geo=None,
        archivos=[ArchivoEvidencia("a.png", "image/png", b"png", "foto")],
    )
    return detalle.siniestro


async def evaluar_hasta(uow, desembolso, sid):
    # Otros avisos de la base compartida pueden estar en la cola: se evalúa hasta tomar el propio.
    for _ in range(50):
        if not await avisos.evaluar_pendientes(uow, desembolso, 20):
            break
    return (await avisos.consultar_detalle(uow, sid)).siniestro


async def test_aviso_persiste_numero_snapshot_y_adjunto(uow):
    s = await registrar(uow)
    detalle = await avisos.consultar_detalle(uow, s.id)

    assert detalle.siniestro.numero.startswith("SIN-")
    assert detalle.siniestro.poliza.ramo == "proteccion-dispositivo"
    assert detalle.adjuntos[0].sha256 and detalle.adjuntos[0].s3_key.endswith(str(detalle.adjuntos[0].id))


async def test_aprobacion_automatica_persiste_traza_sin_duplicados_y_reglas(uow, motor):
    s = await registrar(uow)
    final = await evaluar_hasta(uow, AdaptadorDesembolsoStub(), s.id)

    assert final.estado is EstadoSiniestro.PAGADO
    async with motor.connect() as conn:
        estados = (
            await conn.execute(
                text(f"SELECT estado FROM {ESQUEMA}.siniestro_transicion WHERE siniestro_id = :id ORDER BY ocurrido_en"),
                {"id": s.id},
            )
        ).scalars().all()
        reglas = (
            await conn.execute(
                text(f"SELECT jsonb_array_length(reglas) FROM {ESQUEMA}.siniestro_decision WHERE siniestro_id = :id"),
                {"id": s.id},
            )
        ).scalar_one()
    assert estados == ["recibido", "en_evaluacion", "decidido", "pagado"]
    assert reglas == 6


async def test_retenido_aparece_en_cola_y_operador_decide(uow):
    s = await registrar(uow, ramo="vida-crediticia")
    retenido = await evaluar_hasta(uow, AdaptadorDesembolsoStub(), s.id)
    assert retenido.requiere_revision

    cola = await avisos.filtrar(uow, FiltroSiniestros(requiere_revision=True, limite=100))
    assert s.id in [c.id for c in cola]

    detalle = await avisos.decidir_por_operador(uow, s.id, ResultadoDecision.RECHAZADO, "Falta soporte", "ana")
    assert detalle.siniestro.resultado is ResultadoDecision.RECHAZADO
    assert detalle.decisiones[-1].actor == "ana"


async def test_pago_unico_por_siniestro_en_la_base(uow, motor):
    p = uuid4()
    await registrar(uow, poliza_id=p)
    dup = await registrar(uow, poliza_id=p)
    desembolso = AdaptadorDesembolsoStub()
    await evaluar_hasta(uow, desembolso, dup.id)
    await avisos.decidir_por_operador(uow, dup.id, ResultadoDecision.APROBADO, None, "ana")

    a = await avisos.pagar_siniestro(uow, desembolso, dup.id, "ana")
    b = await avisos.pagar_siniestro(uow, desembolso, dup.id, "ana")

    assert a.pago.comprobante == b.pago.comprobante and b.reintento
    async with motor.connect() as conn:
        pagos = (
            await conn.execute(text(f"SELECT count(*) FROM {ESQUEMA}.pago_siniestro WHERE siniestro_id = :id"), {"id": dup.id})
        ).scalar_one()
    assert pagos == 1
