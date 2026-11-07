"""Casos de uso del siniestro asistido: alta, evaluación asíncrona y cola del operador."""

from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application import avisos
from app.domain.aviso import ArchivoEvidencia
from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada, TransicionInvalida
from app.domain.modelos import EstadoSiniestro, ResultadoDecision, SnapshotPoliza
from app.infrastructure.evidencias import AlmacenEvidenciasEnMemoria
from app.ports.evidencias import ErrorAlmacenEvidencias
from app.ports.persistencia import FiltroSiniestros

HOY = date.today()
PNG = ArchivoEvidencia("dano.png", "image/png", b"\x89PNG-contenido", "foto")


@pytest.fixture
def evidencias() -> AlmacenEvidenciasEnMemoria:
    return AlmacenEvidenciasEnMemoria()


def poliza(ramo="proteccion-dispositivo", estado="vigente", poliza_id=None) -> SnapshotPoliza:
    return SnapshotPoliza(
        poliza_id=poliza_id or uuid4(),
        numero="POL-88421",
        ramo=ramo,
        estado=estado,
        inicio_vigencia=HOY - timedelta(days=60),
        fin_vigencia=HOY + timedelta(days=300),
        suma_asegurada=Decimal("5000000"),
    )


async def registrar(uow, evidencias, *, usuario_id=None, archivos=None, clave=None, **kw):
    detalle, creado = await avisos.registrar_aviso(
        uow,
        evidencias,
        usuario_id=usuario_id or uuid4(),
        poliza=kw.pop("poliza_", None) or poliza(**kw),
        fecha_hecho=HOY - timedelta(days=1),
        descripcion="Pantalla rota",
        canal="web",
        geo=None,
        archivos=[PNG] if archivos is None else archivos,
        clave_idempotencia=clave,
    )
    return detalle, creado


async def test_registrar_guarda_evidencia_en_s3_y_queda_recibido(uow, almacen, evidencias):
    detalle, creado = await registrar(uow, evidencias)

    assert creado
    s = detalle.siniestro
    assert s.estado is EstadoSiniestro.RECIBIDO
    assert s.numero == "SIN-1001"
    assert len(detalle.adjuntos) == 1
    assert detalle.adjuntos[0].s3_key in evidencias.objetos
    assert [e.tipo for e in almacen.eventos] == ["AvisoSiniestroRecibido"]


async def test_si_s3_falla_no_queda_aviso_registrado(uow, almacen, evidencias):
    evidencias.fallar = True
    with pytest.raises(ErrorAlmacenEvidencias):
        await registrar(uow, evidencias)
    assert almacen.siniestros == {}


async def test_aviso_sin_evidencia_se_rechaza(uow, evidencias):
    with pytest.raises(ReglaDeNegocioViolada):
        await registrar(uow, evidencias, archivos=[])


async def test_reintento_con_misma_clave_no_duplica(uow, almacen, evidencias):
    primero, creado1 = await registrar(uow, evidencias, clave="idem-cliente-1")
    segundo, creado2 = await registrar(uow, evidencias, clave="idem-cliente-1")

    assert creado1 and not creado2
    assert segundo.siniestro.id == primero.siniestro.id
    assert len(almacen.siniestros) == 1
    assert len(evidencias.objetos) == 1


async def test_motor_aprueba_y_paga_solo_el_bajo_monto(uow, almacen, evidencias, adaptador_desembolso):
    detalle, _ = await registrar(uow, evidencias)

    procesados = await avisos.evaluar_pendientes(uow, adaptador_desembolso)

    assert procesados == 1
    final = await avisos.consultar_detalle(uow, detalle.siniestro.id)
    s = final.siniestro
    assert s.estado is EstadoSiniestro.PAGADO
    assert s.resultado is ResultadoDecision.APROBADO
    assert s.reserva == Decimal("420000")
    assert [t.estado for t in s.historial] == [
        EstadoSiniestro.RECIBIDO,
        EstadoSiniestro.EN_EVALUACION,
        EstadoSiniestro.DECIDIDO,
        EstadoSiniestro.PAGADO,
    ]
    assert final.decisiones[0].origen.value == "motor"
    assert final.pago.origen.value == "motor"
    assert adaptador_desembolso.desembolsos == [(final.pago.clave_idempotencia, Decimal("420000"))]


async def test_motor_retiene_monto_alto_en_la_cola(uow, evidencias, adaptador_desembolso):
    detalle, _ = await registrar(uow, evidencias, ramo="vida-crediticia")

    await avisos.evaluar_pendientes(uow, adaptador_desembolso)

    s = (await avisos.consultar_detalle(uow, detalle.siniestro.id)).siniestro
    assert s.estado is EstadoSiniestro.EN_EVALUACION
    assert s.requiere_revision is True
    assert "umbral" in s.motivo_revision
    cola = await avisos.filtrar(uow, FiltroSiniestros(requiere_revision=True))
    assert [c.id for c in cola] == [s.id]
    assert adaptador_desembolso.desembolsos == []


async def test_motor_rechaza_poliza_no_vigente(uow, evidencias, adaptador_desembolso):
    detalle, _ = await registrar(uow, evidencias, estado="cancelada")

    await avisos.evaluar_pendientes(uow, adaptador_desembolso)

    s = (await avisos.consultar_detalle(uow, detalle.siniestro.id)).siniestro
    assert s.estado is EstadoSiniestro.DECIDIDO
    assert s.resultado is ResultadoDecision.RECHAZADO


async def test_segundo_aviso_de_la_misma_poliza_queda_retenido_por_antifraude(
    uow, evidencias, adaptador_desembolso
):
    p = poliza()
    await registrar(uow, evidencias, poliza_=p)
    segundo, _ = await registrar(uow, evidencias, poliza_=p)

    await avisos.evaluar_pendientes(uow, adaptador_desembolso)

    final = await avisos.consultar_detalle(uow, segundo.siniestro.id)
    assert final.siniestro.requiere_revision is True
    assert "duplicado" in final.siniestro.motivo_revision
    regla = next(r for r in final.decisiones[0].reglas if r.codigo == "sin_avisos_duplicados")
    assert regla.cumple is False


async def test_falla_del_motor_no_pierde_el_caso(uow, almacen, evidencias, adaptador_desembolso):
    detalle, _ = await registrar(uow, evidencias)
    almacen.parametros = None  # el repositorio de parametría explota al consultar

    await avisos.evaluar_pendientes(uow, adaptador_desembolso)

    final = await avisos.consultar_detalle(uow, detalle.siniestro.id)
    assert final.siniestro.estado is EstadoSiniestro.EN_EVALUACION
    assert final.siniestro.requiere_revision is True
    assert final.decisiones[0].resultado.value == "revision"


async def test_evaluar_dos_veces_no_reprocesa(uow, evidencias, adaptador_desembolso):
    await registrar(uow, evidencias)
    assert await avisos.evaluar_pendientes(uow, adaptador_desembolso) == 1
    assert await avisos.evaluar_pendientes(uow, adaptador_desembolso) == 0
    assert len(adaptador_desembolso.desembolsos) == 1


async def _retenido(uow, evidencias, adaptador_desembolso, **kw):
    detalle, _ = await registrar(uow, evidencias, **kw)
    await avisos.evaluar_pendientes(uow, adaptador_desembolso)
    return detalle.siniestro.id


async def test_operador_rechaza_con_motivo_y_queda_auditado(uow, evidencias, adaptador_desembolso):
    sid = await _retenido(uow, evidencias, adaptador_desembolso, ramo="vida-crediticia")

    final = await avisos.decidir_por_operador(uow, sid, ResultadoDecision.RECHAZADO, "Falta soporte", "ana")

    assert final.siniestro.resultado is ResultadoDecision.RECHAZADO
    auditoria = final.decisiones[-1]
    assert (auditoria.origen.value, auditoria.actor, auditoria.motivo) == ("operador", "ana", "Falta soporte")
    assert final.siniestro.requiere_revision is False


async def test_operador_no_puede_rechazar_sin_motivo(uow, evidencias, adaptador_desembolso):
    sid = await _retenido(uow, evidencias, adaptador_desembolso, ramo="vida-crediticia")
    with pytest.raises(ReglaDeNegocioViolada):
        await avisos.decidir_por_operador(uow, sid, ResultadoDecision.RECHAZADO, "", "ana")
    s = (await avisos.consultar_detalle(uow, sid)).siniestro
    assert s.estado is EstadoSiniestro.EN_EVALUACION
    assert s.requiere_revision is True


async def test_operador_enruta_a_perito(uow, evidencias, adaptador_desembolso):
    sid = await _retenido(uow, evidencias, adaptador_desembolso, ramo="vida-crediticia")
    final = await avisos.enrutar_a_perito(uow, sid, "Requiere inspección", "ana")
    assert final.siniestro.estado is EstadoSiniestro.ENRUTADO
    assert final.decisiones[-1].resultado.value == "enrutado"


async def test_pago_del_operador_es_idempotente_y_traza_el_reintento(uow, evidencias, adaptador_desembolso):
    # Bajo monto retenido por duplicado -> el operador aprueba y paga (HU-29).
    p = poliza()
    await registrar(uow, evidencias, poliza_=p)
    segundo, _ = await registrar(uow, evidencias, poliza_=p)
    await avisos.evaluar_pendientes(uow, adaptador_desembolso)
    sid = segundo.siniestro.id
    await avisos.decidir_por_operador(uow, sid, ResultadoDecision.APROBADO, None, "ana")
    desembolsos_previos = len(adaptador_desembolso.desembolsos)

    primero = await avisos.pagar_siniestro(uow, adaptador_desembolso, sid, "ana")
    reintento = await avisos.pagar_siniestro(uow, adaptador_desembolso, sid, "ana")

    assert not primero.reintento and reintento.reintento
    assert reintento.pago.comprobante == primero.pago.comprobante
    assert len(adaptador_desembolso.desembolsos) == desembolsos_previos + 1
    assert [i.resultado for i in reintento.detalle.intentos_pago] == ["ejecutado", "reintento_idempotente"]
    assert reintento.detalle.siniestro.estado is EstadoSiniestro.PAGADO


async def test_no_se_paga_un_aprobado_sobre_el_umbral(uow, evidencias, adaptador_desembolso):
    sid = await _retenido(uow, evidencias, adaptador_desembolso, ramo="vida-crediticia")
    await avisos.decidir_por_operador(uow, sid, ResultadoDecision.APROBADO, None, "ana")
    with pytest.raises(ReglaDeNegocioViolada) as exc:
        await avisos.pagar_siniestro(uow, adaptador_desembolso, sid, "ana")
    assert exc.value.codigo == "monto_sobre_umbral"


async def test_cliente_no_ve_siniestro_ajeno(uow, evidencias):
    duena = uuid4()
    detalle, _ = await registrar(uow, evidencias, usuario_id=duena)

    assert (await avisos.consultar_detalle(uow, detalle.siniestro.id, duena)).siniestro.id == detalle.siniestro.id
    with pytest.raises(NoEncontrado):
        await avisos.consultar_detalle(uow, detalle.siniestro.id, uuid4())


async def test_decidir_un_caso_ya_decidido_es_conflicto(uow, evidencias, adaptador_desembolso):
    sid = await _retenido(uow, evidencias, adaptador_desembolso, ramo="vida-crediticia")
    await avisos.decidir_por_operador(uow, sid, ResultadoDecision.APROBADO, None, "ana")
    with pytest.raises(TransicionInvalida):
        await avisos.decidir_por_operador(uow, sid, ResultadoDecision.RECHAZADO, "tarde", "luis")
