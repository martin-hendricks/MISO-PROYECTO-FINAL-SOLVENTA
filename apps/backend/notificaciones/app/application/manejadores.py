from __future__ import annotations

import logging
from dataclasses import dataclass
from uuid import UUID

from app.application.casos_uso import crear_notificacion, despachar_notificacion
from app.domain.eventos import EventoBus
from app.domain.modelos import EstadoNotificacion, Notificacion
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.ports.push import EnviadorPush

logger = logging.getLogger(__name__)

TIPOS_SOPORTADOS = frozenset(
    {"PolizaEmitida", "PolizaRenovada", "PolizaModificada", "PolizaCancelada"}
)


@dataclass(frozen=True)
class ContenidoNotificacion:
    tipo: str
    titulo: str
    cuerpo: str
    destino: str


def _texto(payload: dict, clave: str) -> str | None:
    valor = payload.get(clave)
    if isinstance(valor, str) and valor.strip():
        return valor.strip()
    return None


def _sujeto(payload: dict) -> str:
    numero = _texto(payload, "numero")
    return f"La póliza {numero}" if numero else "Tu póliza"


def construir_contenido(evento: EventoBus) -> ContenidoNotificacion | None:
    """Traduce un evento de dominio al texto de la notificación (canal `es-CO`).

    Devuelve `None` para tipos no soportados o eventos sin `payload.usuario_id`.
    """
    if evento.tipo not in TIPOS_SOPORTADOS:
        return None
    if not _texto(evento.payload, "usuario_id"):
        return None

    sujeto = _sujeto(evento.payload)
    fin_vigencia = _texto(evento.payload, "fin_vigencia")

    if evento.tipo == "PolizaEmitida":
        cuerpo = (
            f"{sujeto} está vigente hasta {fin_vigencia}."
            if fin_vigencia
            else f"{sujeto} está vigente."
        )
        return ContenidoNotificacion(
            tipo="poliza_emitida",
            titulo="Tu póliza fue emitida",
            cuerpo=cuerpo,
            destino="aviso-vigencia",
        )

    if evento.tipo == "PolizaRenovada":
        cuerpo = (
            f"{sujeto} ahora vence el {fin_vigencia}."
            if fin_vigencia
            else f"{sujeto} fue renovada."
        )
        return ContenidoNotificacion(
            tipo="poliza_renovada",
            titulo="Tu póliza fue renovada",
            cuerpo=cuerpo,
            destino="aviso-vigencia",
        )

    if evento.tipo == "PolizaModificada":
        return ContenidoNotificacion(
            tipo="poliza_modificada",
            titulo="Actualizamos tus coberturas",
            cuerpo=f"{sujeto} tiene nuevas coberturas.",
            destino="poliza-detalle",
        )

    cuerpo = f"{sujeto} fue cancelada."
    devolucion = _texto(evento.payload, "devolucion_estimada")
    if devolucion:
        cuerpo += f" Devolución estimada: {devolucion}."
    return ContenidoNotificacion(
        tipo="poliza_cancelada",
        titulo="Tu póliza fue cancelada",
        cuerpo=cuerpo,
        destino="poliza-detalle",
    )


async def manejar_evento(
    uow: FabricaUnidadDeTrabajo, push: EnviadorPush, evento: EventoBus
) -> Notificacion | None:
    """Convierte un evento del bus en notificación push y la despacha.

    Idempotente por `(evento_id, "push")`: repetir el mensaje no duplica la
    notificación ni el push. Nunca propaga excepciones para no detener el
    consumo de la partición.
    """
    contenido = construir_contenido(evento)
    if contenido is None:
        logger.warning(
            "evento_ignorado",
            extra={"evento_id": str(evento.evento_id), "tipo": evento.tipo},
        )
        return None

    try:
        usuario_id = UUID(str(evento.payload.get("usuario_id")))
    except (TypeError, ValueError, AttributeError):
        logger.warning(
            "evento_con_usuario_invalido",
            extra={"evento_id": str(evento.evento_id), "tipo": evento.tipo},
        )
        return None

    try:
        notificacion = await crear_notificacion(
            uow,
            usuario_id=usuario_id,
            evento_origen_id=evento.evento_id,
            canal="push",
            tipo=contenido.tipo,
            titulo=contenido.titulo,
            cuerpo=contenido.cuerpo,
            destino=contenido.destino,
        )
        if notificacion.estado == EstadoNotificacion.PENDIENTE.value:
            await despachar_notificacion(uow, push, notificacion.notificacion_id)
            # despachar_notificacion actualiza su propia instancia dentro de
            # otra unidad de trabajo y devuelve solo un bool -- hay que
            # releer para que el estado (enviada/fallida) quede reflejado en
            # el valor que se retorna aquí, no en la instancia ya obsoleta
            # que `crear_notificacion` devolvió antes de despachar.
            async with uow() as tx:
                actualizada = await tx.notificaciones.obtener(notificacion.notificacion_id)
            if actualizada is not None:
                return actualizada
        return notificacion
    except Exception:
        logger.exception(
            "error_manejando_evento",
            extra={"evento_id": str(evento.evento_id), "tipo": evento.tipo},
        )
        return None
