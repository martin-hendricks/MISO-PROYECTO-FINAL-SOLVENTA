from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from .errores import ReglaDeNegocioViolada, TransicionInvalida

if TYPE_CHECKING:
    from app.ports.catalogo import CatalogoProductos


class EstadoSolicitud(StrEnum):
    RECIBIDA = "recibida"
    COTIZADA = "cotizada"
    RECHAZADA = "rechazada"


@dataclass
class SolicitudCotizacion:
    id: UUID
    idempotency_key: str
    usuario_id: UUID
    socio_id: UUID
    consentimiento_id: UUID
    producto: str
    canal: str
    datos_riesgo: dict[str, Any]
    estado: EstadoSolicitud
    creada_en: datetime

    @classmethod
    def crear(
        cls,
        idempotency_key: str,
        usuario_id: UUID,
        socio_id: UUID,
        consentimiento_id: UUID,
        producto: str,
        canal: str,
        datos_riesgo: dict[str, Any],
        catalogo: "CatalogoProductos",
    ) -> SolicitudCotizacion:
        definicion = catalogo.obtener(producto)
        if definicion is None:
            raise ReglaDeNegocioViolada("producto_no_encontrado", f"Producto '{producto}' no existe en el catálogo")

        for campo, regla in definicion.datos_riesgo.items():
            if campo not in datos_riesgo:
                raise ReglaDeNegocioViolada(
                    "dato_riesgo_faltante", f"Falta el dato de riesgo obligatorio '{campo}'"
                )
            valor = datos_riesgo[campo]
            if not regla.valido(valor):
                raise ReglaDeNegocioViolada(
                    "dato_riesgo_fuera_de_rango",
                    f"'{campo}' fuera de rango: {regla.describir_rango()}",
                )

        return cls(
            id=uuid4(),
            idempotency_key=idempotency_key,
            usuario_id=usuario_id,
            socio_id=socio_id,
            consentimiento_id=consentimiento_id,
            producto=producto,
            canal=canal,
            datos_riesgo=datos_riesgo,
            estado=EstadoSolicitud.RECIBIDA,
            creada_en=datetime.now(UTC),
        )

    def marcar_cotizada(self) -> None:
        if self.estado is not EstadoSolicitud.RECIBIDA:
            raise TransicionInvalida(self.estado, EstadoSolicitud.COTIZADA)
        self.estado = EstadoSolicitud.COTIZADA


@dataclass(frozen=True)
class EventoDominio:
    tipo: str
    agregado_id: UUID
    payload: dict
    id: UUID = field(default_factory=uuid4)


def solicitud_recibida(solicitud: SolicitudCotizacion) -> EventoDominio:
    return EventoDominio(
        tipo="SolicitudCotizacionRecibida",
        agregado_id=solicitud.id,
        payload={
            "solicitud_id": str(solicitud.id),
            "producto": solicitud.producto,
            "usuario_id": str(solicitud.usuario_id),
        },
    )
