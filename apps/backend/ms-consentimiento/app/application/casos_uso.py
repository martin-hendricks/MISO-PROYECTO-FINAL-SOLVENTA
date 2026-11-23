from __future__ import annotations

from dataclasses import dataclass

from app.domain.errores import NoEncontrado
from app.domain.modelos import Consentimiento
from app.ports.persistencia import FabricaUnidadDeTrabajo


@dataclass(frozen=True)
class RegistroConsentimiento:
    consentimiento: Consentimiento
    creado: bool


async def otorgar_consentimiento(uow: FabricaUnidadDeTrabajo, cliente_id: str) -> RegistroConsentimiento:
    """Otorgamiento idempotente: si el cliente ya tiene un consentimiento
    vigente, lo devuelve sin crear uno nuevo (`creado=False`, 200 en la
    API). Solo crea uno nuevo si no hay ninguno vigente (`creado=True`, 201).

    Nota de stub: no publica ningún evento de dominio. Este servicio no
    propaga el otorgamiento/revocación al resto de la plataforma por su
    cuenta — ver el aviso completo en app/domain/modelos.py."""
    async with uow() as tx:
        vigente = await tx.consentimientos.obtener_vigente(cliente_id)
        if vigente is not None:
            return RegistroConsentimiento(vigente, creado=False)

        consentimiento = Consentimiento.otorgar(cliente_id)
        await tx.consentimientos.agregar(consentimiento)
        await tx.confirmar()
    return RegistroConsentimiento(consentimiento, creado=True)


async def consultar_consentimiento_vigente(uow: FabricaUnidadDeTrabajo, cliente_id: str) -> Consentimiento:
    async with uow() as tx:
        vigente = await tx.consentimientos.obtener_vigente(cliente_id)
    if vigente is None:
        raise NoEncontrado(f"El cliente {cliente_id} no tiene consentimiento de habeas data vigente")
    return vigente


async def revocar_consentimiento(uow: FabricaUnidadDeTrabajo, cliente_id: str) -> Consentimiento:
    """Revoca el consentimiento vigente del cliente. Solo marca
    `revocado_en`; no borra el registro (queda como evidencia de que
    existió) y no notifica a nadie más — la siguiente lectura de
    `obtener_vigente`/`consultar_consentimiento_vigente` ya no lo
    encuentra, porque se lee siempre el último estado persistido (sin
    caché intermedia), pero cualquier sistema que haya cacheado el dato
    por su cuenta no se entera de este cambio."""
    async with uow() as tx:
        vigente = await tx.consentimientos.obtener_vigente(cliente_id)
        if vigente is None:
            raise NoEncontrado(f"El cliente {cliente_id} no tiene consentimiento de habeas data vigente")
        vigente.revocar()
        await tx.consentimientos.actualizar(vigente)
        await tx.confirmar()
    return vigente


__all__ = [
    "RegistroConsentimiento",
    "otorgar_consentimiento",
    "consultar_consentimiento_vigente",
    "revocar_consentimiento",
]
