from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import Pago, clave_cobro_prima, pago_prima_registrado
from app.ports.externos import PasarelaPagos, VerificadorSuscripcion
from app.ports.persistencia import ClaveIdempotenciaDuplicada, FabricaUnidadDeTrabajo


@dataclass(frozen=True)
class SolicitudCobro:
    solicitud_id: UUID
    oferta_id: UUID
    usuario_id: UUID
    monto: Decimal
    token_medio_pago: str


@dataclass(frozen=True)
class Cobro:
    pago: Pago
    creado: bool


async def cobrar_prima(
    uow: FabricaUnidadDeTrabajo,
    suscripciones: VerificadorSuscripcion,
    pasarela: PasarelaPagos,
    solicitud: SolicitudCobro,
) -> Cobro:
    clave = clave_cobro_prima(solicitud.oferta_id)
    # Un reintento con la misma clave devuelve el resultado original sin volver a cobrar.
    async with uow() as tx:
        existente = await tx.pagos.obtener_por_clave(clave)
    if existente is not None:
        return Cobro(existente, creado=False)

    Pago.validar_monto(solicitud.monto)
    if not await suscripciones.aceptada(solicitud.solicitud_id):
        raise ReglaDeNegocioViolada(
            "suscripcion_no_aceptada", "Solo se cobra la prima de una suscripción aceptada"
        )

    resultado = await pasarela.cobrar(solicitud.token_medio_pago, solicitud.monto, clave)
    pago = Pago.registrar_prima(solicitud.oferta_id, solicitud.usuario_id, solicitud.monto, resultado)
    async with uow() as tx:
        await tx.pagos.agregar(pago, solicitud.token_medio_pago)
        await tx.outbox.agregar(pago_prima_registrado(pago))
        try:
            await tx.confirmar()
            return Cobro(pago, creado=True)
        except ClaveIdempotenciaDuplicada:
            pass

    async with uow() as tx:
        ganador = await tx.pagos.obtener_por_clave(clave)
    if ganador is None:
        raise RuntimeError("Clave duplicada sin pago visible")
    return Cobro(ganador, creado=False)


async def consultar_pago(uow: FabricaUnidadDeTrabajo, pago_id: UUID) -> Pago:
    async with uow() as tx:
        pago = await tx.pagos.obtener(pago_id)
    if pago is None:
        raise NoEncontrado(f"El pago {pago_id} no existe")
    return pago
