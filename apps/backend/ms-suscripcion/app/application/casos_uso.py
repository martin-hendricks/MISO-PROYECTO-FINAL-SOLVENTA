from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.errores import NoEncontrado, ReglaNoConfigurada
from app.domain.modelos import Suscripcion, suscripcion_decidida
from app.ports.persistencia import FabricaUnidadDeTrabajo, SolicitudYaDecidida


@dataclass(frozen=True)
class Resultado:
    suscripcion: Suscripcion
    creada: bool


async def evaluar_suscripcion(
    uow: FabricaUnidadDeTrabajo, solicitud_id: UUID, perfil_id: UUID, score: Decimal
) -> Resultado:
    """Decide automáticamente (sin underwriter). Idempotente por solicitud: un
    reintento devuelve la decisión ya persistida, nunca una nueva."""
    async with uow() as tx:
        existente = await tx.suscripciones.obtener_por_solicitud(solicitud_id)
        if existente is not None:
            return Resultado(existente, creada=False)

        regla = await tx.reglas.vigente()
        if regla is None:
            raise ReglaNoConfigurada("No hay una regla de suscripción vigente")

        suscripcion = Suscripcion.decidir(solicitud_id, perfil_id, score, regla)
        await tx.suscripciones.agregar(suscripcion)
        await tx.outbox.agregar(suscripcion_decidida(suscripcion))
        try:
            await tx.confirmar()
            return Resultado(suscripcion, creada=True)
        except SolicitudYaDecidida:
            pass

    async with uow() as tx:
        ganadora = await tx.suscripciones.obtener_por_solicitud(solicitud_id)
    if ganadora is None:
        raise RuntimeError("Solicitud duplicada sin decisión visible")
    return Resultado(ganadora, creada=False)


async def consultar_suscripcion(uow: FabricaUnidadDeTrabajo, solicitud_id: UUID) -> Suscripcion:
    async with uow() as tx:
        suscripcion = await tx.suscripciones.obtener_por_solicitud(solicitud_id)
    if suscripcion is None:
        raise NoEncontrado(f"La solicitud {solicitud_id} no tiene decisión de suscripción")
    return suscripcion
