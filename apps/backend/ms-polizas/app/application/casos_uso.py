from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from uuid import UUID

from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import (
    Cobertura,
    Poliza,
    numero_de_poliza,
    poliza_cancelada,
    poliza_emitida,
    poliza_modificada,
    poliza_renovada,
)
from app.ports.persistencia import FabricaUnidadDeTrabajo, PolizaYaEmitida
from app.ports.precondiciones import VerificadorCobro, VerificadorSuscripcion


@dataclass(frozen=True)
class SolicitudEmision:
    solicitud_id: UUID
    oferta_id: UUID
    usuario_id: UUID
    token_pago_confirmado: UUID
    coberturas: list[Cobertura]


@dataclass(frozen=True)
class Emision:
    poliza: Poliza
    creada: bool


def _hoy() -> date:
    return datetime.now(UTC).date()


async def emitir_poliza(
    uow: FabricaUnidadDeTrabajo,
    suscripciones: VerificadorSuscripcion,
    cobros: VerificadorCobro,
    solicitud: SolicitudEmision,
) -> Emision:
    # Reintentar sobre la misma oferta devuelve la póliza ya emitida, sin volver a validar ni numerar.
    async with uow() as tx:
        existente = await tx.polizas.obtener_por_oferta(solicitud.oferta_id)
    if existente is not None:
        return Emision(existente, creada=False)

    if not await suscripciones.aceptada(solicitud.solicitud_id):
        raise ReglaDeNegocioViolada(
            "suscripcion_no_aceptada", "La póliza solo se emite sobre una suscripción aceptada"
        )
    if not await cobros.exitoso(solicitud.oferta_id, solicitud.token_pago_confirmado):
        raise ReglaDeNegocioViolada("cobro_no_exitoso", "La póliza solo se emite con el cobro de la prima exitoso")

    async with uow() as tx:
        hoy = _hoy()
        numero = numero_de_poliza(hoy.year, await tx.polizas.siguiente_secuencia())
        poliza = Poliza.emitir(solicitud.oferta_id, solicitud.usuario_id, numero, solicitud.coberturas, hoy)
        await tx.polizas.agregar(poliza)
        await tx.outbox.agregar(poliza_emitida(poliza))
        try:
            await tx.confirmar()
            return Emision(poliza, creada=True)
        except PolizaYaEmitida:
            pass

    async with uow() as tx:
        ganadora = await tx.polizas.obtener_por_oferta(solicitud.oferta_id)
    if ganadora is None:
        raise RuntimeError("Oferta duplicada sin póliza visible")
    return Emision(ganadora, creada=False)


async def consultar_poliza(uow: FabricaUnidadDeTrabajo, poliza_id: UUID) -> Poliza:
    async with uow() as tx:
        poliza = await tx.polizas.obtener(poliza_id)
    if poliza is None:
        raise NoEncontrado(f"La póliza {poliza_id} no existe")
    return poliza


async def consultar_poliza_por_numero(uow: FabricaUnidadDeTrabajo, numero: str) -> Poliza:
    async with uow() as tx:
        poliza = await tx.polizas.obtener_por_numero(numero)
    if poliza is None:
        raise NoEncontrado(f"La póliza {numero} no existe")
    return poliza


async def listar_polizas_de_usuario(uow: FabricaUnidadDeTrabajo, usuario_id: UUID, limite: int) -> list[Poliza]:
    async with uow() as tx:
        return await tx.polizas.listar_por_usuario(usuario_id, limite)


async def _obtener_o_fallar(tx, poliza_id: UUID) -> Poliza:
    poliza = await tx.polizas.obtener(poliza_id)
    if poliza is None:
        raise NoEncontrado(f"La póliza {poliza_id} no existe")
    return poliza


async def renovar_poliza(uow: FabricaUnidadDeTrabajo, poliza_id: UUID, nueva_fin_vigencia: date) -> Poliza:
    """HU-59: extiende la vigencia. Lanza NoEncontrado si la póliza no existe
    y TransicionInvalida (vía Poliza.renovar) si no está VIGENTE."""
    async with uow() as tx:
        poliza = await _obtener_o_fallar(tx, poliza_id)
        poliza.renovar(nueva_fin_vigencia)
        await tx.polizas.actualizar(poliza)
        await tx.outbox.agregar(poliza_renovada(poliza))
        await tx.confirmar()
        return poliza


async def modificar_poliza(uow: FabricaUnidadDeTrabajo, poliza_id: UUID, nuevas_coberturas: list[Cobertura]) -> Poliza:
    """HU-60: reemplaza las coberturas. Lanza NoEncontrado si la póliza no
    existe y TransicionInvalida/ReglaDeNegocioViolada (vía
    Poliza.modificar_coberturas) si no está VIGENTE o las coberturas son inválidas."""
    async with uow() as tx:
        poliza = await _obtener_o_fallar(tx, poliza_id)
        poliza.modificar_coberturas(nuevas_coberturas)
        await tx.polizas.actualizar(poliza)
        await tx.outbox.agregar(poliza_modificada(poliza))
        await tx.confirmar()
        return poliza


async def cancelar_poliza(uow: FabricaUnidadDeTrabajo, poliza_id: UUID, motivo: str) -> Poliza:
    """HU-61: única transición de estado real del ciclo de vida. Lanza
    NoEncontrado si la póliza no existe y TransicionInvalida (vía
    Poliza.cancelar) si ya estaba cancelada."""
    async with uow() as tx:
        poliza = await _obtener_o_fallar(tx, poliza_id)
        poliza.cancelar(motivo, _hoy())
        await tx.polizas.actualizar(poliza)
        await tx.outbox.agregar(poliza_cancelada(poliza))
        await tx.confirmar()
        return poliza
