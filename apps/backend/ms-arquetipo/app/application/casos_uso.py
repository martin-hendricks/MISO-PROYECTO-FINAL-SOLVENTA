from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from app.domain.errores import NoEncontrado
from app.domain.modelos import Ejemplo, ejemplo_aprobado, ejemplo_registrado
from app.ports.persistencia import ClaveIdempotenciaDuplicada, FabricaUnidadDeTrabajo


@dataclass(frozen=True)
class Registro:
    ejemplo: Ejemplo
    creado: bool


@dataclass(frozen=True)
class Indicadores:
    total: int
    monto_total: Decimal


async def registrar_ejemplo(
    uow: FabricaUnidadDeTrabajo, idempotency_key: str, referencia: str, monto: Decimal
) -> Registro:
    async with uow() as tx:
        existente = await tx.ejemplos.obtener_por_clave(idempotency_key)
        if existente is not None:
            return Registro(existente, creado=False)

        ejemplo = Ejemplo.registrar(idempotency_key, referencia, monto)
        await tx.ejemplos.agregar(ejemplo)
        await tx.outbox.agregar(ejemplo_registrado(ejemplo))
        try:
            await tx.confirmar()
            return Registro(ejemplo, creado=True)
        except ClaveIdempotenciaDuplicada:
            pass

    async with uow() as tx:
        ganador = await tx.ejemplos.obtener_por_clave(idempotency_key)
    if ganador is None:
        raise RuntimeError("Clave duplicada sin registro visible")
    return Registro(ganador, creado=False)


async def consultar_ejemplo(uow: FabricaUnidadDeTrabajo, ejemplo_id: UUID) -> Ejemplo:
    async with uow() as tx:
        ejemplo = await tx.ejemplos.obtener(ejemplo_id)
    if ejemplo is None:
        raise NoEncontrado(f"Ejemplo {ejemplo_id} no existe")
    return ejemplo


async def listar_ejemplos(uow: FabricaUnidadDeTrabajo, limite: int) -> list[Ejemplo]:
    async with uow() as tx:
        return await tx.ejemplos.listar(limite)


async def calcular_indicadores(uow: FabricaUnidadDeTrabajo) -> Indicadores:
    async with uow() as tx:
        total, monto = await tx.ejemplos.indicadores()
    return Indicadores(total=total, monto_total=monto)


async def aprobar_ejemplo(uow: FabricaUnidadDeTrabajo, ejemplo_id: UUID) -> Ejemplo:
    async with uow() as tx:
        ejemplo = await tx.ejemplos.obtener(ejemplo_id)
        if ejemplo is None:
            raise NoEncontrado(f"Ejemplo {ejemplo_id} no existe")
        ejemplo.aprobar()
        await tx.ejemplos.actualizar(ejemplo)
        await tx.outbox.agregar(ejemplo_aprobado(ejemplo))
        await tx.confirmar()
    return ejemplo
