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


class TokenEntrada(BaseModel):
    token: str


class AudienciaUsuarioSalida(BaseModel):
    usuarioId: UUID
    dispositivosActivos: int


class AudienciaSalida(BaseModel):
    usuarios: list[AudienciaUsuarioSalida]


class AudienciaEntrada(BaseModel):
    tipo: str
    usuarioIds: list[UUID] = []


class DifusionEntrada(BaseModel):
    titulo: str
    cuerpo: str
    audiencia: AudienciaEntrada
    poliza: str | None = None


class DifusionSalida(BaseModel):
    difusionId: UUID
    titulo: str
    cuerpo: str
    poliza: str | None
    creadaEn: datetime
    enviadas: int
    fallidas: int
    sinDispositivo: int

    @classmethod
    def desde(cls, difusion) -> "DifusionSalida":
        return cls(
            difusionId=difusion.difusion_id,
            titulo=difusion.titulo,
            cuerpo=difusion.cuerpo,
            poliza=difusion.poliza,
            creadaEn=difusion.creada_en,
            enviadas=difusion.enviadas,
            fallidas=difusion.fallidas,
            sinDispositivo=difusion.sin_dispositivo,
        )


class DifusionCreadaSalida(BaseModel):
    difusionId: UUID
    enviadas: int
    fallidas: int
    sinDispositivo: int


class HistorialSalida(BaseModel):
    items: list[DifusionSalida]


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
