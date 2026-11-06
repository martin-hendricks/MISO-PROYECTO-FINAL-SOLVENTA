from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.errores import NoEncontrado, ServicioExternoNoDisponible
from app.domain.modelos import DispositivoPush, Notificacion
from app.ports.persistencia import (
    DispositivoDuplicado,
    FabricaUnidadDeTrabajo,
    NotificacionDuplicada,
)
from app.ports.push import EnviadorPush


@dataclass(frozen=True)
class DispositivoRegistrado:
    """Resultado del upsert: el dispositivo y si fue creado (para responder 201 vs 200).

    Delega los atributos del dispositivo para que el caso de uso también pueda usarse
    como si devolviera directamente el `DispositivoPush`.
    """

    dispositivo: DispositivoPush
    creado: bool

    def __getattr__(self, nombre: str):
        return getattr(self.dispositivo, nombre)


async def registrar_dispositivo(
    uow: FabricaUnidadDeTrabajo, usuario_id: UUID, plataforma: str, token: str
) -> DispositivoRegistrado:
    """Upsert idempotente por (usuario_id, token); reactiva un dispositivo desactivado."""
    nuevo = DispositivoPush.registrar(usuario_id, plataforma, token)

    async with uow() as tx:
        existente = await tx.dispositivos.obtener_por_usuario_token(usuario_id, nuevo.token)
        if existente is not None:
            existente.plataforma = nuevo.plataforma
            existente.activar()
            await tx.dispositivos.actualizar(existente)
            await tx.confirmar()
            return DispositivoRegistrado(existente, creado=False)

        await tx.dispositivos.agregar(nuevo)
        try:
            await tx.confirmar()
            return DispositivoRegistrado(nuevo, creado=True)
        except DispositivoDuplicado:
            pass

    async with uow() as tx:
        ganador = await tx.dispositivos.obtener_por_usuario_token(usuario_id, nuevo.token)
    if ganador is None:
        raise RuntimeError("Dispositivo duplicado sin registro visible")
    return DispositivoRegistrado(ganador, creado=False)


async def desactivar_dispositivo(
    uow: FabricaUnidadDeTrabajo, usuario_id: UUID, dispositivo_id: UUID
) -> None:
    async with uow() as tx:
        dispositivo = await tx.dispositivos.obtener(dispositivo_id)
        if dispositivo is None or dispositivo.usuario_id != usuario_id:
            raise NoEncontrado(f"Dispositivo {dispositivo_id} no existe")
        if dispositivo.activo:
            dispositivo.desactivar()
            await tx.dispositivos.actualizar(dispositivo)
            await tx.confirmar()


async def listar_notificaciones(
    uow: FabricaUnidadDeTrabajo,
    usuario_id: UUID,
    limite: int,
    antes_de: datetime | None = None,
) -> list[Notificacion]:
    async with uow() as tx:
        return await tx.notificaciones.listar(usuario_id, limite, antes_de)


async def consultar_notificacion(
    uow: FabricaUnidadDeTrabajo, usuario_id: UUID, notificacion_id: UUID
) -> Notificacion:
    async with uow() as tx:
        notificacion = await tx.notificaciones.obtener(notificacion_id)
    if notificacion is None or notificacion.usuario_id != usuario_id:
        raise NoEncontrado(f"Notificación {notificacion_id} no existe")
    return notificacion


async def marcar_leida(
    uow: FabricaUnidadDeTrabajo, usuario_id: UUID, notificacion_id: UUID
) -> Notificacion:
    async with uow() as tx:
        notificacion = await tx.notificaciones.obtener(notificacion_id)
        if notificacion is None or notificacion.usuario_id != usuario_id:
            raise NoEncontrado(f"Notificación {notificacion_id} no existe")
        notificacion.marcar_leida(datetime.now(UTC))
        await tx.notificaciones.actualizar(notificacion)
        await tx.confirmar()
    return notificacion


async def crear_notificacion(
    uow: FabricaUnidadDeTrabajo,
    usuario_id: UUID,
    evento_origen_id: UUID | None,
    canal: str,
    tipo: str,
    titulo: str,
    cuerpo: str,
    destino: str | None = None,
) -> Notificacion:
    """Idempotente por (evento_origen_id, canal): repetir el evento no duplica la notificación."""
    nueva = Notificacion.crear(
        usuario_id=usuario_id,
        evento_origen_id=evento_origen_id,
        canal=canal,
        tipo=tipo,
        titulo=titulo,
        cuerpo=cuerpo,
        destino=destino,
    )

    async with uow() as tx:
        if evento_origen_id is not None:
            existente = await tx.notificaciones.obtener_por_evento_canal(
                evento_origen_id, nueva.canal
            )
            if existente is not None:
                return existente

        await tx.notificaciones.agregar(nueva)
        try:
            await tx.confirmar()
            return nueva
        except NotificacionDuplicada:
            pass

    async with uow() as tx:
        ganadora = await tx.notificaciones.obtener_por_evento_canal(evento_origen_id, nueva.canal)
    if ganadora is None:
        raise RuntimeError("Notificación duplicada sin registro visible")
    return ganadora


async def despachar_pendientes(
    uow: FabricaUnidadDeTrabajo,
    push: EnviadorPush,
    usuario_id: UUID | None = None,
) -> int:
    """Envía las notificaciones push pendientes. Devuelve cuántas quedaron enviadas.

    Lo invocará el consumidor de MSK; no se arranca en esta tarea. Las fallidas no se
    reintentan automáticamente para no repetir pushes ya entregados.
    """
    async with uow() as tx:
        pendientes = await tx.notificaciones.listar_pendientes_push(usuario_id)

    enviadas = 0
    for pendiente in pendientes:
        async with uow() as tx:
            notificacion = await tx.notificaciones.obtener(pendiente.notificacion_id)
            if notificacion is None or notificacion.estado != "pendiente":
                continue

            dispositivos = await tx.dispositivos.listar_activos(notificacion.usuario_id)
            if not dispositivos:
                notificacion.marcar_fallida()
                await tx.notificaciones.actualizar(notificacion)
                await tx.confirmar()
                continue

            try:
                proveedores = await push.enviar_a_usuario(dispositivos, notificacion)
            except ServicioExternoNoDisponible:
                notificacion.marcar_fallida()
                await tx.notificaciones.actualizar(notificacion)
                await tx.confirmar()
                continue

            if not proveedores:
                notificacion.marcar_fallida()
                await tx.notificaciones.actualizar(notificacion)
                await tx.confirmar()
                continue

            notificacion.marcar_enviada(proveedores[0])
            await tx.notificaciones.actualizar(notificacion)
            await tx.confirmar()
            enviadas += 1

    return enviadas
