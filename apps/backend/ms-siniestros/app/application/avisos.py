"""Casos de uso del siniestro asistido (HU-157 y relacionadas).

Flujo (PDF §5.1 #3 con aprobación asíncrona):
1. registrar_aviso: guarda la evidencia en S3 y el aviso en RECIBIDO. Responde al instante.
2. evaluar_pendientes (worker): el motor aprueba y paga el bajo monto, rechaza lo objetivo
   o retiene para el operador lo que no puede resolver.
3. decidir_por_operador / enrutar_a_perito / pagar_siniestro: la cola del back-office.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from app.domain import motor_reglas
from app.domain.aviso import (
    Adjunto,
    ArchivoEvidencia,
    Decision,
    IntentoPago,
    OrigenDecision,
    PagoSiniestro,
    ParametroRamo,
    ResultadoAuditado,
    aviso_recibido,
    decision_registrada,
    pago_siniestro_realizado,
    validar_cantidad_adjuntos,
)
from app.domain.errores import NoEncontrado
from app.domain.modelos import (
    EstadoSiniestro,
    Geo,
    ResultadoDecision,
    Siniestro,
    SnapshotPoliza,
    siniestro_cambio_estado,
)
from app.ports.evidencias import AlmacenEvidencias
from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import ClaveIdempotenciaDuplicada, FabricaUnidadDeTrabajo, FiltroSiniestros

log = logging.getLogger(__name__)

ACTOR_MOTOR = "motor-reglas-siniestros"


@dataclass(frozen=True)
class DetalleSiniestro:
    siniestro: Siniestro
    adjuntos: list[Adjunto]
    decisiones: list[Decision]
    pago: PagoSiniestro | None
    intentos_pago: list[IntentoPago]


@dataclass(frozen=True)
class ResultadoPago:
    pago: PagoSiniestro
    reintento: bool
    detalle: DetalleSiniestro


async def _detalle(tx, siniestro: Siniestro) -> DetalleSiniestro:
    return DetalleSiniestro(
        siniestro=siniestro,
        adjuntos=await tx.adjuntos.listar_de(siniestro.id),
        decisiones=await tx.decisiones.listar_de(siniestro.id),
        pago=await tx.pagos_siniestro.obtener_de(siniestro.id),
        intentos_pago=await tx.pagos_siniestro.listar_intentos(siniestro.id),
    )


async def _obtener_o_falla(tx, siniestro_id: UUID, usuario_id: UUID | None = None) -> Siniestro:
    siniestro = await tx.siniestros.obtener(siniestro_id)
    # Un cliente nunca ve un siniestro ajeno: se responde igual que si no existiera.
    if siniestro is None or (usuario_id is not None and siniestro.usuario_id != usuario_id):
        raise NoEncontrado(f"Siniestro {siniestro_id} no existe")
    return siniestro


async def registrar_aviso(
    uow: FabricaUnidadDeTrabajo,
    almacen: AlmacenEvidencias,
    *,
    usuario_id: UUID,
    poliza: SnapshotPoliza,
    fecha_hecho: date,
    descripcion: str,
    canal: str,
    geo: Geo | None,
    archivos: list[ArchivoEvidencia],
    lugar: str | None = None,
    clave_idempotencia: str | None = None,
) -> tuple[DetalleSiniestro, bool]:
    """Alta del aviso (N5) con su evidencia (N6). Devuelve (detalle, creado). Con la misma
    clave de idempotencia un reintento devuelve el aviso original (creado=False), sin
    duplicar el siniestro ni la evidencia."""
    if clave_idempotencia:
        async with uow() as tx:
            existente = await tx.siniestros.obtener_por_clave_idempotencia(clave_idempotencia)
            if existente is not None:
                return await _detalle(tx, existente), False

    validar_cantidad_adjuntos(archivos)
    siniestro = Siniestro.avisar(
        usuario_id=usuario_id,
        poliza=poliza,
        fecha_hecho=fecha_hecho,
        descripcion=descripcion,
        canal=canal,
        geo=geo,
        lugar=lugar,
        clave_idempotencia=clave_idempotencia,
    )
    adjuntos = [Adjunto.desde_archivo(a, siniestro, almacen.bucket) for a in archivos]

    # Primero S3, después la base: si S3 falla no queda un aviso que apunte a evidencia
    # inexistente. Si la base falla después, quedan objetos huérfanos (sin referencia),
    # que no exponen nada porque el bucket es privado.
    for adjunto, archivo in zip(adjuntos, archivos, strict=True):
        await almacen.guardar(adjunto.s3_key, archivo.contenido, adjunto.content_type)

    async with uow() as tx:
        await tx.siniestros.agregar(siniestro)
        for adjunto in adjuntos:
            await tx.adjuntos.agregar(adjunto)
        await tx.outbox.agregar(aviso_recibido(siniestro))
        try:
            await tx.confirmar()
        except ClaveIdempotenciaDuplicada:
            if not clave_idempotencia:
                raise
            creado = False
        else:
            return DetalleSiniestro(siniestro, adjuntos, [], None, []), True

    # Perdió la carrera de idempotencia contra otro request con la misma clave.
    async with uow() as tx:
        ganador = await tx.siniestros.obtener_por_clave_idempotencia(clave_idempotencia)
        if ganador is None:
            raise RuntimeError("Clave de idempotencia duplicada sin aviso visible")
        return await _detalle(tx, ganador), creado


async def consultar_detalle(
    uow: FabricaUnidadDeTrabajo, siniestro_id: UUID, usuario_id: UUID | None = None
) -> DetalleSiniestro:
    async with uow() as tx:
        return await _detalle(tx, await _obtener_o_falla(tx, siniestro_id, usuario_id))


async def filtrar(uow: FabricaUnidadDeTrabajo, filtro: FiltroSiniestros) -> list[Siniestro]:
    async with uow() as tx:
        return await tx.siniestros.filtrar(filtro)


async def listar_parametros(uow: FabricaUnidadDeTrabajo) -> list[ParametroRamo]:
    async with uow() as tx:
        return await tx.parametros.listar()


async def evaluar_pendientes(
    uow: FabricaUnidadDeTrabajo, adaptador_desembolso: AdaptadorDesembolso, limite: int = 20
) -> int:
    """Una pasada del worker asíncrono. Cada aviso se evalúa en su propia transacción: si
    uno falla, los demás siguen, y el que falló sigue en RECIBIDO para la próxima pasada."""
    procesados = 0
    for _ in range(limite):
        try:
            async with uow() as tx:
                pendientes = await tx.siniestros.tomar_pendientes_de_evaluacion(1)
                if not pendientes:
                    break
                await _evaluar_uno(tx, pendientes[0], adaptador_desembolso)
                await tx.confirmar()
                procesados += 1
        except Exception:  # noqa: BLE001 - el worker no debe morir por un aviso
            log.exception("No se pudo evaluar un aviso pendiente; se reintenta en la próxima pasada")
            break
    return procesados


async def _evaluar_uno(tx, siniestro: Siniestro, adaptador_desembolso: AdaptadorDesembolso) -> None:
    siniestro.tomar_para_evaluacion(ACTOR_MOTOR)
    await _registrar_transicion(tx, siniestro)

    try:
        parametro = await tx.parametros.obtener(siniestro.poliza.ramo)
        ventana = parametro.ventana_duplicado_dias if parametro else 30
        previos = await tx.siniestros.contar_avisos_de_poliza_desde(
            siniestro.poliza_id, datetime.now(UTC) - timedelta(days=ventana), excluir=siniestro.id
        )
        adjuntos = await tx.adjuntos.listar_de(siniestro.id)
        resultado = motor_reglas.evaluar(siniestro, parametro, len(adjuntos), previos)
    except Exception as exc:  # noqa: BLE001
        # §6.3: la falla del motor no pierde el caso; un humano lo resuelve.
        log.exception("Motor de reglas falló para %s", siniestro.id)
        siniestro.retener_para_revision("Motor de reglas no disponible")
        decision = Decision.registrar(
            siniestro.id, OrigenDecision.MOTOR, ACTOR_MOTOR, ResultadoAuditado.REVISION,
            f"Motor de reglas no disponible: {type(exc).__name__}",
        )
        await tx.siniestros.actualizar(siniestro)
        await tx.decisiones.agregar(decision)
        await tx.outbox.agregar(decision_registrada(siniestro, decision))
        return

    siniestro.reserva = resultado.reserva
    siniestro.umbral_automatico = resultado.umbral_automatico
    decision = Decision.registrar(
        siniestro.id, OrigenDecision.MOTOR, ACTOR_MOTOR, resultado.resultado, resultado.motivo, resultado.reglas
    )

    if resultado.resultado is ResultadoAuditado.REVISION:
        siniestro.retener_para_revision(resultado.motivo)
        await tx.siniestros.actualizar(siniestro)
    else:
        siniestro.decidir(ResultadoDecision(resultado.resultado.value), resultado.motivo, ACTOR_MOTOR)
        await _registrar_transicion(tx, siniestro)

    await tx.decisiones.agregar(decision)
    await tx.outbox.agregar(decision_registrada(siniestro, decision))

    # Conciliación acordada: el bajo monto aprobado por el motor se paga solo.
    if resultado.resultado is ResultadoAuditado.APROBADO:
        await _ejecutar_pago(tx, siniestro, adaptador_desembolso, OrigenDecision.MOTOR, ACTOR_MOTOR)


async def _registrar_transicion(tx, siniestro: Siniestro) -> None:
    await tx.siniestros.actualizar(siniestro)
    await tx.outbox.agregar(siniestro_cambio_estado(siniestro, siniestro.historial[-1]))


async def _ejecutar_pago(
    tx, siniestro: Siniestro, adaptador: AdaptadorDesembolso, origen: OrigenDecision, actor: str
) -> PagoSiniestro:
    pago = PagoSiniestro.autorizar(siniestro, origen, actor)
    await adaptador.desembolsar(pago.clave_idempotencia, pago.monto)
    await tx.pagos_siniestro.agregar(pago)
    await tx.pagos_siniestro.registrar_intento(
        IntentoPago(siniestro.id, pago.clave_idempotencia, "ejecutado", pago.comprobante, actor)
    )
    siniestro.cambiar_estado(EstadoSiniestro.PAGADO, actor)
    await _registrar_transicion(tx, siniestro)
    await tx.outbox.agregar(pago_siniestro_realizado(pago))
    return pago


async def decidir_por_operador(
    uow: FabricaUnidadDeTrabajo,
    siniestro_id: UUID,
    resultado: ResultadoDecision,
    motivo: str | None,
    actor: str,
) -> DetalleSiniestro:
    """HU-27: aprobar o rechazar con auditoría. Aprobar NO paga: el pago de bajo monto es
    una acción explícita del operador (HU-29, pagar_siniestro)."""
    async with uow() as tx:
        siniestro = await _obtener_o_falla(tx, siniestro_id)
        siniestro.decidir(resultado, motivo, f"operador:{actor}")
        decision = Decision.registrar(
            siniestro.id, OrigenDecision.OPERADOR, actor, ResultadoAuditado(resultado.value), motivo
        )
        await _registrar_transicion(tx, siniestro)
        await tx.decisiones.agregar(decision)
        await tx.outbox.agregar(decision_registrada(siniestro, decision))
        await tx.confirmar()
        return await _detalle(tx, siniestro)


async def enrutar_a_perito(
    uow: FabricaUnidadDeTrabajo, siniestro_id: UUID, motivo: str | None, actor: str
) -> DetalleSiniestro:
    """HU-28: el caso complejo sale de la cola hacia un perito."""
    async with uow() as tx:
        siniestro = await _obtener_o_falla(tx, siniestro_id)
        siniestro.enrutar_a_perito(f"operador:{actor}")
        decision = Decision.registrar(
            siniestro.id, OrigenDecision.OPERADOR, actor, ResultadoAuditado.ENRUTADO, motivo
        )
        await _registrar_transicion(tx, siniestro)
        await tx.decisiones.agregar(decision)
        await tx.outbox.agregar(decision_registrada(siniestro, decision))
        await tx.confirmar()
        return await _detalle(tx, siniestro)


async def pagar_siniestro(
    uow: FabricaUnidadDeTrabajo, adaptador: AdaptadorDesembolso, siniestro_id: UUID, actor: str
) -> ResultadoPago:
    """HU-29: desembolso de bajo monto, una sola vez. Un reintento devuelve el mismo
    comprobante, no mueve dinero y queda en la traza como reintento_idempotente."""
    async with uow() as tx:
        siniestro = await _obtener_o_falla(tx, siniestro_id)
        existente = await tx.pagos_siniestro.obtener_de(siniestro.id)
        if existente is None:
            pago = await _ejecutar_pago(tx, siniestro, adaptador, OrigenDecision.OPERADOR, actor)
            try:
                await tx.confirmar()
            except ClaveIdempotenciaDuplicada:
                pass  # otro request pagó primero: se trata como reintento abajo
            else:
                return ResultadoPago(pago, False, await _detalle(tx, siniestro))

    async with uow() as tx:
        siniestro = await _obtener_o_falla(tx, siniestro_id)
        pago = await tx.pagos_siniestro.obtener_de(siniestro.id)
        if pago is None:
            raise RuntimeError("Pago duplicado sin registro visible")
        await tx.pagos_siniestro.registrar_intento(
            IntentoPago(siniestro.id, pago.clave_idempotencia, "reintento_idempotente", pago.comprobante, actor)
        )
        await tx.confirmar()
        return ResultadoPago(pago, True, await _detalle(tx, siniestro))
