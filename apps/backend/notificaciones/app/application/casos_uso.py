from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada, ServicioExternoNoDisponible
from app.domain.modelos import Difusion, DispositivoPush, Notificacion, resolver_audiencia
from app.ports.persistencia import (
    DispositivoDuplicado,
    FabricaUnidadDeTrabajo,
    NotificacionDuplicada,
)
from app.ports.push import EnviadorPush, EstadoEnvio


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


async def desactivar_dispositivo_por_token(
    uow: FabricaUnidadDeTrabajo, usuario_id: UUID, token: str
) -> None:
    """204 aunque el token no exista: el cierre de sesión se puede repetir."""
    token_limpio = (token or "").strip()
    if not token_limpio:
        raise ReglaDeNegocioViolada("token_vacio", "El token del dispositivo es obligatorio")
    async with uow() as tx:
        dispositivo = await tx.dispositivos.obtener_por_usuario_token(usuario_id, token_limpio)
        if dispositivo is not None and dispositivo.activo:
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
    poliza: str | None = None,
    difusion_id: UUID | None = None,
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
        poliza=poliza,
        difusion_id=difusion_id,
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


async def despachar_notificacion(
    uow: FabricaUnidadDeTrabajo,
    push: EnviadorPush,
    notificacion_id: UUID,
) -> bool:
    """Envía una notificación push concreta. Devuelve si quedó enviada.

    Solo actúa sobre notificaciones `pendiente`: una ya enviada, fallida o leída no se
    reenvía, de modo que repetir el evento de origen no duplica el push.
    """
    async with uow() as tx:
        notificacion = await tx.notificaciones.obtener(notificacion_id)
        if notificacion is None or notificacion.estado != "pendiente":
            return False

        dispositivos = await tx.dispositivos.listar_activos(notificacion.usuario_id)
        if not dispositivos:
            notificacion.marcar_fallida()
            await tx.notificaciones.actualizar(notificacion)
            await tx.confirmar()
            return False

        try:
            resultados = await push.enviar_a_usuario(dispositivos, notificacion)
        except ServicioExternoNoDisponible:
            notificacion.marcar_fallida()
            await tx.notificaciones.actualizar(notificacion)
            await tx.confirmar()
            return False

        for resultado in resultados:
            if resultado.estado != EstadoEnvio.TOKEN_INVALIDO:
                continue
            dispositivo = next(
                (d for d in dispositivos if d.dispositivo_id == resultado.dispositivo_id),
                None,
            )
            if dispositivo is not None and dispositivo.activo:
                dispositivo.desactivar()
                await tx.dispositivos.actualizar(dispositivo)

        enviados = [r for r in resultados if r.estado == EstadoEnvio.ENVIADO and r.proveedor_id]
        if not enviados:
            notificacion.marcar_fallida()
            await tx.notificaciones.actualizar(notificacion)
            await tx.confirmar()
            return False

        notificacion.marcar_enviada(enviados[0].proveedor_id)
        await tx.notificaciones.actualizar(notificacion)
        await tx.confirmar()
        return True


async def despachar_pendientes(
    uow: FabricaUnidadDeTrabajo,
    push: EnviadorPush,
    usuario_id: UUID | None = None,
) -> int:
    """Envía las notificaciones push pendientes. Devuelve cuántas quedaron enviadas.

    Las fallidas no se reintentan automáticamente para no repetir pushes ya entregados.
    """
    async with uow() as tx:
        pendientes = await tx.notificaciones.listar_pendientes_push(usuario_id)

    enviadas = 0
    for pendiente in pendientes:
        if await despachar_notificacion(uow, push, pendiente.notificacion_id):
            enviadas += 1

    return enviadas


@dataclass(frozen=True)
class ResultadoDifusion:
    difusion_id: UUID
    enviadas: int
    fallidas: int
    sin_dispositivo: int


async def listar_audiencia(
    uow: FabricaUnidadDeTrabajo, usuario_ids: list[UUID] | None
) -> list[tuple[UUID, int]]:
    async with uow() as tx:
        return await tx.dispositivos.contar_activos(usuario_ids)


async def difundir(
    uow: FabricaUnidadDeTrabajo,
    push: EnviadorPush,
    autor_id: UUID,
    titulo: str,
    cuerpo: str,
    tipo_audiencia: str,
    usuario_ids: list[UUID] | None,
    poliza: str | None,
) -> ResultadoDifusion:
    audiencia, ids = resolver_audiencia(tipo_audiencia, usuario_ids)
    # Valida título, cuerpo y póliza antes de escribir filas.
    Difusion.crear(autor_id, titulo, cuerpo, audiencia, destinatarios=0, poliza=poliza)

    async with uow() as tx:
        conteos = await tx.dispositivos.contar_activos(None if audiencia == "todos" else ids)
        con_dispositivo = {usuario_id for usuario_id, cantidad in conteos if cantidad > 0}
        if audiencia == "todos":
            objetivos = sorted(con_dispositivo, key=str)
            sin_dispositivo = 0
            destinatarios = len(objetivos)
        else:
            objetivos = [usuario_id for usuario_id in ids if usuario_id in con_dispositivo]
            sin_dispositivo = len(ids) - len(objetivos)
            destinatarios = len(ids)
        difusion = Difusion.crear(
            autor_id, titulo, cuerpo, audiencia, destinatarios, poliza=poliza
        )
        await tx.difusiones.agregar(difusion)
        creadas: list[Notificacion] = []
        for usuario_id in objetivos:
            notificacion = Notificacion.crear(
                usuario_id=usuario_id,
                evento_origen_id=None,
                canal="push",
                tipo="mensaje_operador",
                titulo=difusion.titulo,
                cuerpo=difusion.cuerpo,
                destino="poliza-detalle" if difusion.poliza else "inicio",
                poliza=difusion.poliza,
                difusion_id=difusion.difusion_id,
            )
            await tx.notificaciones.agregar(notificacion)
            creadas.append(notificacion)
        await tx.confirmar()

    semaforo = asyncio.Semaphore(20)

    async def _enviar(notificacion_id: UUID) -> bool:
        async with semaforo:
            return await despachar_notificacion(uow, push, notificacion_id)

    resultados = await asyncio.gather(*[_enviar(n.notificacion_id) for n in creadas])
    enviadas = sum(1 for ok in resultados if ok)
    fallidas = len(resultados) - enviadas

    async with uow() as tx:
        await tx.difusiones.actualizar_totales(
            difusion.difusion_id, enviadas, fallidas, sin_dispositivo
        )
        await tx.confirmar()
    return ResultadoDifusion(difusion.difusion_id, enviadas, fallidas, sin_dispositivo)


async def listar_difusiones(
    uow: FabricaUnidadDeTrabajo, limite: int, antes_de: datetime | None
) -> list[Difusion]:
    async with uow() as tx:
        return await tx.difusiones.listar(limite, antes_de)
