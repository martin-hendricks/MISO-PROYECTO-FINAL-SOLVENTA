from __future__ import annotations

import time
from dataclasses import dataclass, replace
from decimal import Decimal
from uuid import UUID

from app.domain.errores import NoEncontrado
from app.domain.modelos import (
    EstadoSiniestro,
    EvaluacionUmbral,
    EventoParametrico,
    PagoParametrico,
    PagoRecibido,
    Siniestro,
    evento_parametrico_recibido,
    pago_parametrico_disparado,
    siniestro_cambio_estado,
    umbral_evaluado,
)
from app.metricas_negocio import LATENCIA, RESULTADO
from app.ports.pagos import AdaptadorDesembolso
from app.ports.persistencia import ClaveIdempotenciaDuplicada, FabricaUnidadDeTrabajo

ORIGEN_SISTEMA = "ms-siniestros:evaluacion-paramétrica"
ORIGEN_INGESTA_HTTP = "stub-evento-parametrico"
ORIGEN_TOPICO_TELEMETRIA = "topico-telemetria"


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
        await _transicionar(tx, siniestro, nuevo_estado, origen)
        await tx.confirmar()
    return siniestro


async def consultar_siniestro(
    uow: FabricaUnidadDeTrabajo, siniestro_id: UUID, usuario_id: UUID | None = None
) -> Siniestro:
    async with uow() as tx:
        siniestro = await tx.siniestros.obtener(siniestro_id)
    if siniestro is None or (usuario_id is not None and siniestro.usuario_id != usuario_id):
        raise NoEncontrado(f"Siniestro {siniestro_id} no existe")
    return siniestro


async def listar_siniestros(
    uow: FabricaUnidadDeTrabajo, limite: int, usuario_id: UUID | None = None
) -> list[Siniestro]:
    async with uow() as tx:
        return await tx.siniestros.listar(limite, usuario_id)


@dataclass(frozen=True)
class PagosRecibidos:
    moneda: str | None
    total: Decimal | None
    pagos: list[PagoRecibido]


def resumir_pagos_recibidos(pagos: list[PagoRecibido]) -> PagosRecibidos:
    """Un total solo cuando cada depósito nombra la misma moneda. Sin filas, el total es cero en COP."""
    monedas = {pago.moneda for pago in pagos}
    if len(monedas) > 1:
        return PagosRecibidos(moneda=None, total=None, pagos=pagos)
    moneda = next(iter(monedas), "COP")
    return PagosRecibidos(
        moneda=moneda, total=sum((pago.monto for pago in pagos), Decimal("0.00")), pagos=pagos
    )


async def listar_pagos_recibidos(uow: FabricaUnidadDeTrabajo, usuario_id: UUID) -> PagosRecibidos:
    async with uow() as tx:
        pagos = await tx.siniestros.listar_pagos_recibidos(usuario_id)
    return resumir_pagos_recibidos(pagos)


async def obtener_pago_recibido(uow: FabricaUnidadDeTrabajo, siniestro_id: UUID, usuario_id: UUID) -> PagoRecibido:
    async with uow() as tx:
        pago = await tx.siniestros.obtener_pago_recibido(siniestro_id, usuario_id)
    if pago is None:
        raise NoEncontrado(f"Pago {siniestro_id} no existe")
    return pago


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
    usuario_id: UUID | None = None,
    ramo: str | None = None,
    poliza_numero: str | None = None,
    descripcion: str | None = None,
    origen: str = ORIGEN_INGESTA_HTTP,
) -> ResultadoIngesta:
    """HU-32 -> HU-33 -> HU-34 en dos pasos, con el efecto externo entre ellos.

    1. Una sola transacción registra el evento y el siniestro, lo evalúa y, si
       corresponde, deja el pago registrado con el siniestro en ENRUTADO. Si algo falla
       antes del commit no queda nada persistido y la reingesta procesa desde cero.
    2. Después del commit se desembolsa y otra transacción cierra en PAGADO. Solo se
       desembolsa un pago ya confirmado en la base, y PAGADO significa que el
       desembolso ocurrió.

    Si el proceso cae entre el commit y el desembolso, el siniestro queda en ENRUTADO con
    el pago registrado: la reingesta del mismo evento_id (reintento del proveedor o
    reentrega del tópico) completa el desembolso. Una entrega concurrente que llega
    mientras el ganador aún está en ENRUTADO también lo intenta: la llamada al adaptador
    es "al menos una vez", siempre con la misma clave evento_id, y el adaptador es
    idempotente por esa clave. Esa idempotencia es la que impide el pago doble.
    """
    inicio = time.perf_counter()
    evento = EventoParametrico.recibir(evento_id, valor)

    resultado = await _registrar_y_decidir(
        uow,
        evento,
        umbral,
        poliza_vigente,
        monto_pago,
        origen,
        poliza_id,
        usuario_id,
        ramo,
        poliza_numero,
        descripcion,
    )
    if resultado.procesado:
        LATENCIA.labels("registro").observe(time.perf_counter() - inicio)
        if resultado.pago is None:
            RESULTADO.labels("no_pagado").inc()

    if resultado.pago is not None and resultado.siniestro.estado is EstadoSiniestro.ENRUTADO:
        siniestro = await _completar_pago(uow, adaptador_desembolso, resultado.siniestro.id, resultado.pago)
        resultado = replace(resultado, siniestro=siniestro)
        if resultado.procesado:
            LATENCIA.labels("hasta_pago").observe(time.perf_counter() - inicio)
    return resultado


async def _registrar_y_decidir(
    uow: FabricaUnidadDeTrabajo,
    evento: EventoParametrico,
    umbral: Decimal,
    poliza_vigente: bool,
    monto_pago: Decimal,
    origen: str,
    poliza_id: UUID | None,
    usuario_id: UUID | None,
    ramo: str | None,
    poliza_numero: str | None,
    descripcion: str | None,
) -> ResultadoIngesta:
    """Paso 1: todo en una transacción. Idempotente por evento_id (HU-32)."""
    async with uow() as tx:
        existente = await tx.eventos_parametricos.obtener_por_clave(evento.evento_id)
        if existente is not None:
            return await _resultado_existente(tx, existente)

        try:
            siniestro = Siniestro.recibir(
                evento.evento_id,
                origen=origen,
                poliza_id=poliza_id,
                usuario_id=usuario_id,
                ramo=ramo,
                poliza_numero=poliza_numero,
                descripcion=descripcion,
            )
            # El evento va primero: su PK es la clave de idempotencia, así una colisión
            # concurrente se detecta antes de escribir el siniestro.
            await tx.eventos_parametricos.agregar(evento)
            await tx.siniestros.agregar(siniestro)
            await tx.outbox.agregar(evento_parametrico_recibido(evento, siniestro))

            await _transicionar(tx, siniestro, EstadoSiniestro.EN_EVALUACION, ORIGEN_SISTEMA)
            evaluacion = await _evaluar(tx, evento, siniestro, umbral, poliza_vigente)
            await _transicionar(tx, siniestro, EstadoSiniestro.DECIDIDO, ORIGEN_SISTEMA)

            pago: PagoParametrico | None = None
            if evaluacion.decision:
                await _transicionar(tx, siniestro, EstadoSiniestro.ENRUTADO, ORIGEN_SISTEMA)
                pago = await _registrar_pago(tx, siniestro.id, evaluacion, monto_pago)

            await tx.confirmar()
            return ResultadoIngesta(siniestro, evento, evaluacion, pago, procesado=True)
        except ClaveIdempotenciaDuplicada:
            pass

    # Perdió la carrera: otra transacción ya registró este evento_id.
    async with uow() as tx:
        ganador = await tx.eventos_parametricos.obtener_por_clave(evento.evento_id)
        if ganador is None:
            raise RuntimeError("Clave de evento duplicada sin registro visible")
        return await _resultado_existente(tx, ganador)


async def _completar_pago(
    uow: FabricaUnidadDeTrabajo,
    adaptador_desembolso: AdaptadorDesembolso,
    siniestro_id: UUID,
    pago: PagoParametrico,
) -> Siniestro:
    """Paso 2: desembolso fuera de la transacción y cierre en PAGADO."""
    await adaptador_desembolso.desembolsar(pago.evento_id, pago.monto)
    async with uow() as tx:
        siniestro = await tx.siniestros.obtener(siniestro_id)
        if siniestro is None:
            raise NoEncontrado(f"Siniestro {siniestro_id} no existe")
        if siniestro.estado is EstadoSiniestro.PAGADO:
            return siniestro  # otra entrega del mismo evento ya lo cerró
        await _transicionar(tx, siniestro, EstadoSiniestro.PAGADO, ORIGEN_SISTEMA)
        await tx.confirmar()
    RESULTADO.labels("pagado").inc()
    return siniestro


async def _transicionar(tx, siniestro: Siniestro, estado: EstadoSiniestro, origen: str) -> None:
    siniestro.cambiar_estado(estado, origen)
    await tx.siniestros.actualizar(siniestro)
    await tx.outbox.agregar(siniestro_cambio_estado(siniestro, siniestro.historial[-1]))


async def _evaluar(
    tx, evento: EventoParametrico, siniestro: Siniestro, umbral: Decimal, poliza_vigente: bool
) -> EvaluacionUmbral:
    evaluacion = EvaluacionUmbral.evaluar(evento, umbral, poliza_vigente)
    await tx.evaluaciones.agregar(evaluacion)
    await tx.outbox.agregar(umbral_evaluado(evaluacion, siniestro))
    return evaluacion


async def _registrar_pago(tx, siniestro_id: UUID, evaluacion: EvaluacionUmbral, monto: Decimal) -> PagoParametrico:
    pago = PagoParametrico.disparar(evaluacion, siniestro_id, monto)
    await tx.pagos.agregar(pago)
    await tx.outbox.agregar(pago_parametrico_disparado(pago))
    return pago


async def evaluar_umbral(
    uow: FabricaUnidadDeTrabajo, evento: EventoParametrico, umbral: Decimal, poliza_vigente: bool
) -> EvaluacionUmbral:
    """HU-33 aislada: compara el valor del evento contra el umbral que viaja en la
    solicitud (no se llama por red a ms-polizas). El resultado (umbral, valor, decisión
    y motivo) queda persistido siempre, se pague o no."""
    async with uow() as tx:
        siniestro = await tx.siniestros.obtener_por_evento(evento.evento_id)
        if siniestro is None:
            raise NoEncontrado(f"No existe siniestro para el evento {evento.evento_id}")
        evaluacion = await _evaluar(tx, evento, siniestro, umbral, poliza_vigente)
        await tx.confirmar()
    return evaluacion


async def disparar_pago_parametrico(
    uow: FabricaUnidadDeTrabajo,
    adaptador_desembolso: AdaptadorDesembolso,
    siniestro_id: UUID,
    evaluacion: EvaluacionUmbral,
    monto: Decimal,
) -> PagoParametrico:
    """HU-34 aislada: registra el pago y desembolsa DESPUÉS del commit. Idempotente por
    evento_id: si el pago ya existe se reintenta el desembolso (el adaptador lo absorbe)
    y se devuelve el pago original."""
    async with uow() as tx:
        pago = await tx.pagos.obtener_por_evento(evaluacion.evento_id)
        if pago is None:
            pago = await _registrar_pago(tx, siniestro_id, evaluacion, monto)
            try:
                await tx.confirmar()
            except ClaveIdempotenciaDuplicada:
                pago = None

    if pago is None:
        async with uow() as tx:
            pago = await tx.pagos.obtener_por_evento(evaluacion.evento_id)
        if pago is None:
            raise RuntimeError("Clave de pago duplicada sin registro visible")

    await adaptador_desembolso.desembolsar(pago.evento_id, pago.monto)
    return pago


async def _resultado_existente(tx, evento: EventoParametrico) -> ResultadoIngesta:
    siniestro = await tx.siniestros.obtener_por_evento(evento.evento_id)
    evaluacion = await tx.evaluaciones.obtener_por_evento(evento.evento_id)
    pago = await tx.pagos.obtener_por_evento(evento.evento_id)
    if siniestro is None or evaluacion is None:
        raise RuntimeError(f"Evento {evento.evento_id} ingerido sin evaluación visible")
    return ResultadoIngesta(siniestro, evento, evaluacion, pago, procesado=False)
