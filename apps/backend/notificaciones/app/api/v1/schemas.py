from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.domain.modelos import DispositivoPush, Notificacion


class RegistrarDispositivoEntrada(BaseModel):
    plataforma: str
    token: str


class DispositivoSalida(BaseModel):
    dispositivo_id: UUID
    usuario_id: UUID
    plataforma: str
    activo: bool

    @classmethod
    def desde(cls, dispositivo: DispositivoPush) -> "DispositivoSalida":
        return cls(
            dispositivo_id=dispositivo.dispositivo_id,
            usuario_id=dispositivo.usuario_id,
            plataforma=dispositivo.plataforma,
            activo=dispositivo.activo,
        )


class NotificacionSalida(BaseModel):
    notificacion_id: UUID
    usuario_id: UUID
    evento_origen_id: UUID | None
    canal: str
    tipo: str
    titulo: str
    cuerpo: str
    destino: str | None
    estado: str
    creada_en: datetime
    enviada_en: datetime | None
    leida_en: datetime | None

    @classmethod
    def desde(cls, notificacion: Notificacion) -> "NotificacionSalida":
        return cls(
            notificacion_id=notificacion.notificacion_id,
            usuario_id=notificacion.usuario_id,
            evento_origen_id=notificacion.evento_origen_id,
            canal=notificacion.canal,
            tipo=notificacion.tipo,
            titulo=notificacion.titulo,
            cuerpo=notificacion.cuerpo,
            destino=notificacion.destino,
            estado=notificacion.estado,
            creada_en=notificacion.creada_en,
            enviada_en=notificacion.enviada_en,
            leida_en=notificacion.leida_en,
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
