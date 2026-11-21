from __future__ import annotations

from uuid import UUID

from app.domain.errores import NoEncontrado
from app.domain.socios import CredencialSocio, Socio
from app.ports.persistencia import FabricaUnidadDeTrabajo


async def _obtener(tx, socio_id: UUID) -> Socio:
    socio = await tx.socios.obtener(socio_id)
    if socio is None:
        raise NoEncontrado("Socio no encontrado")
    return socio


async def crear_socio(
    uow: FabricaUnidadDeTrabajo, nombre: str, alcances: frozenset[str]
) -> tuple[Socio, CredencialSocio, str]:
    socio, credencial, api_key = Socio.nuevo(nombre, alcances)
    async with uow() as tx:
        await tx.socios.agregar(socio)
        await tx.confirmar()
    return socio, credencial, api_key


async def listar_socios(uow: FabricaUnidadDeTrabajo) -> list[Socio]:
    async with uow() as tx:
        return await tx.socios.listar()


async def emitir_credencial(
    uow: FabricaUnidadDeTrabajo, socio_id: UUID
) -> tuple[CredencialSocio, str]:
    async with uow() as tx:
        socio = await _obtener(tx, socio_id)
        credencial, api_key = socio.emitir_credencial()
        await tx.socios.actualizar(socio)
        await tx.confirmar()
    return credencial, api_key


async def revocar_credencial(
    uow: FabricaUnidadDeTrabajo, socio_id: UUID, credencial_id: UUID
) -> None:
    async with uow() as tx:
        socio = await _obtener(tx, socio_id)
        socio.revocar_credencial(credencial_id)
        await tx.socios.actualizar(socio)
        await tx.confirmar()


async def revocar_socio(uow: FabricaUnidadDeTrabajo, socio_id: UUID) -> Socio:
    async with uow() as tx:
        socio = await _obtener(tx, socio_id)
        socio.revocar()
        await tx.socios.actualizar(socio)
        await tx.confirmar()
    return socio


async def resolver_por_huella(uow: FabricaUnidadDeTrabajo, huella_sha256: str) -> Socio:
    async with uow() as tx:
        socio = await tx.socios.obtener_por_huella(huella_sha256)
    if socio is None or not socio.acepta(huella_sha256):
        raise NoEncontrado("Socio no encontrado")
    return socio
