from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.errores import NoEncontrado
from app.domain.modelos import (
    EstadoSiniestro,
    EvaluacionUmbral,
    EventoParametrico,
    PagoParametrico,
    Siniestro,
    evento_parametrico_recibido,
    pago_parametrico_disparado,
    siniestro_cambio_estado,
    umbral_evaluado,
)
from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import ClaveIdempotenciaDuplicada, FabricaUnidadDeTrabajo

ORIGEN_SISTEMA = "ms-siniestros:evaluacion-paramétrica"


@dataclass(frozen=True)
class ResultadoIngesta:
    siniestro: Siniestro
    evento: EventoParametrico
    evaluacion: EvaluacionUmbral
    pago: PagoParametrico | None
    procesado: bool
    """False cuando el evento ya había sido ingerido antes (reingesta idempotente)."""


async def cambiar_estado_siniestro(
    uow: FabricaUnidadDeTrabajo, siniestro_id: UUID, nuevo_estado: EstadoSiniestro, origen: str
) -> Siniestro:
    """HU-30: aplica una transición de estado validada por el agregado. Si la transición
    es inválida, Siniestro.cambiar_estado lanza TransicionInvalida ANTES de mutar nada,
    así que no hay commit ni estado intermedio persistido (atomicidad)."""
    async with uow() as tx:
        siniestro = await tx.siniestros.obtener(siniestro_id)
        if siniestro is None:
            raise NoEncontrado(f"Siniestro {siniestro_id} no existe")
        siniestro.cambiar_estado(nuevo_estado, origen)
        await tx.siniestros.actualizar(siniestro)
        await tx.outbox.agregar(siniestro_cambio_estado(siniestro, siniestro.historial[-1]))
        await tx.confirmar()
    return siniestro


async def consultar_siniestro(uow: FabricaUnidadDeTrabajo, siniestro_id: UUID) -> Siniestro:
    async with uow() as tx:
        siniestro = await tx.siniestros.obtener(siniestro_id)
    if siniestro is None:
        raise NoEncontrado(f"Siniestro {siniestro_id} no existe")
    return siniestro


async def listar_siniestros(uow: FabricaUnidadDeTrabajo, limite: int) -> list[Siniestro]:
    async with uow() as tx:
        return await tx.siniestros.listar(limite)


async def listar_siniestros_abiertos_de_poliza(uow: FabricaUnidadDeTrabajo, poliza_id: UUID) -> list[Siniestro]:
    """HU-61 (back-office): siniestros de la póliza que no llegaron a PAGADO,
    el único estado terminal del enum -- usado por ms-polizas/bff-web como
    dato informativo antes de cancelar (no bloquea la cancelación)."""
    async with uow() as tx:
        return await tx.siniestros.listar_abiertos_por_poliza(poliza_id)


async def recibir_evento_parametrico(
    uow: FabricaUnidadDeTrabajo,
    adaptador_desembolso: AdaptadorDesembolso,
    evento_id: str,
    valor: Decimal,
    umbral: Decimal,
    poliza_vigente: bool,
    monto_pago: Decimal,
    poliza_id: UUID | None = None,
) -> ResultadoIngesta:
    """Encadena HU-32 (ingesta idempotente) -> HU-33 (evaluación de umbral) -> HU-34
    (pago paramétrico stub) en una sola invocación desde la ruta de ingesta, pero cada
    paso vive en su propia función testeable (evaluar_umbral / disparar_pago_parametrico)
    para que puedan probarse de forma aislada.

    Idempotencia por evento_id (HU-32): si el evento ya fue ingerido, NO se vuelve a
    evaluar ni se genera un segundo pago; se devuelve el resultado ya persistido.
    """
    evento = EventoParametrico.recibir(evento_id, valor)

    async with uow() as tx:
        existente = await tx.eventos_parametricos.obtener_por_clave(evento.evento_id)
        if existente is not None:
            return await _resultado_existente(tx, existente)

        siniestro = Siniestro.recibir(evento.evento_id, origen="stub-evento-parametrico", poliza_id=poliza_id)
        await tx.siniestros.agregar(siniestro)
        await tx.eventos_parametricos.agregar(evento)
        await tx.outbox.agregar(evento_parametrico_recibido(evento, siniestro))

        try:
            await tx.confirmar()
            ingerido = True
        except ClaveIdempotenciaDuplicada:
            ingerido = False

    if ingerido:
        return await _evaluar_y_pagar(uow, adaptador_desembolso, siniestro, evento, umbral, poliza_vigente, monto_pago)

    # Perdió la carrera de idempotencia: otra transacción ya ingirió este evento_id.
    async with uow() as tx:
        ganador = await tx.eventos_parametricos.obtener_por_clave(evento.evento_id)
        if ganador is None:
            raise RuntimeError("Clave de evento duplicada sin registro visible")
        return await _resultado_existente(tx, ganador)


async def _evaluar_y_pagar(
    uow: FabricaUnidadDeTrabajo,
    adaptador_desembolso: AdaptadorDesembolso,
    siniestro: Siniestro,
    evento: EventoParametrico,
    umbral: Decimal,
    poliza_vigente: bool,
    monto_pago: Decimal,
) -> ResultadoIngesta:
    await cambiar_estado_siniestro(uow, siniestro.id, EstadoSiniestro.EN_EVALUACION, ORIGEN_SISTEMA)
    evaluacion = await evaluar_umbral(uow, evento, umbral, poliza_vigente)
    siniestro = await cambiar_estado_siniestro(uow, siniestro.id, EstadoSiniestro.DECIDIDO, ORIGEN_SISTEMA)

    pago: PagoParametrico | None = None
    if evaluacion.decision:
        siniestro = await cambiar_estado_siniestro(uow, siniestro.id, EstadoSiniestro.ENRUTADO, ORIGEN_SISTEMA)
        pago = await disparar_pago_parametrico(uow, adaptador_desembolso, siniestro.id, evaluacion, monto_pago)
        siniestro = await cambiar_estado_siniestro(uow, siniestro.id, EstadoSiniestro.PAGADO, ORIGEN_SISTEMA)

    return ResultadoIngesta(siniestro, evento, evaluacion, pago, procesado=True)


async def evaluar_umbral(
    uow: FabricaUnidadDeTrabajo, evento: EventoParametrico, umbral: Decimal, poliza_vigente: bool
) -> EvaluacionUmbral:
    """HU-33: compara el valor del evento contra el umbral que viaja en la solicitud de
    evaluación (no se llama por red a ms-polizas). El resultado (umbral, valor, decisión
    y motivo) queda persistido siempre, se pague o no."""
    async with uow() as tx:
        siniestro = await tx.siniestros.obtener_por_evento(evento.evento_id)
        if siniestro is None:
            raise NoEncontrado(f"No existe siniestro para el evento {evento.evento_id}")
        evaluacion = EvaluacionUmbral.evaluar(evento, umbral, poliza_vigente)
        await tx.evaluaciones.agregar(evaluacion)
        await tx.outbox.agregar(umbral_evaluado(evaluacion, siniestro))
        await tx.confirmar()
    return evaluacion


async def disparar_pago_parametrico(
    uow: FabricaUnidadDeTrabajo,
    adaptador_desembolso: AdaptadorDesembolso,
    siniestro_id: UUID,
    evaluacion: EvaluacionUmbral,
    monto: Decimal,
) -> PagoParametrico:
    """HU-34: dispara el desembolso simulado sin intervención humana cuando el umbral se
    cumplió. Idempotente por evento_id: si ya existe un pago para ese evento, se
    devuelve el pago original sin generar un segundo desembolso."""
    async with uow() as tx:
        existente = await tx.pagos.obtener_por_evento(evaluacion.evento_id)
        if existente is not None:
            return existente

        pago = PagoParametrico.disparar(evaluacion, siniestro_id, monto)
        await adaptador_desembolso.desembolsar(pago.evento_id, pago.monto)
        await tx.pagos.agregar(pago)
        await tx.outbox.agregar(pago_parametrico_disparado(pago))

        try:
            await tx.confirmar()
        except ClaveIdempotenciaDuplicada:
            pass
        else:
            return pago

    async with uow() as tx:
        ganador = await tx.pagos.obtener_por_evento(evaluacion.evento_id)
    if ganador is None:
        raise RuntimeError("Clave de pago duplicada sin registro visible")
    return ganador


async def _resultado_existente(tx, evento: EventoParametrico) -> ResultadoIngesta:
    siniestro = await tx.siniestros.obtener_por_evento(evento.evento_id)
    evaluacion = await tx.evaluaciones.obtener_por_evento(evento.evento_id)
    pago = await tx.pagos.obtener_por_evento(evento.evento_id)
    if siniestro is None or evaluacion is None:
        raise RuntimeError(f"Evento {evento.evento_id} ingerido sin evaluación visible")
    return ResultadoIngesta(siniestro, evento, evaluacion, pago, procesado=False)
