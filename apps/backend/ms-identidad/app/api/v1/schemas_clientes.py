from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import Usuario


class DocumentoSalida(BaseModel):
    tipo: str
    numero: str


class ClienteSalida(BaseModel):
    """Shape de cliente para el back-office (HU-141). `estado` y
    `consentimiento` van en minúsculas a propósito: bff-web (y detrás de
    él, el frontend) los consume tal cual, sin tener que traducir el
    EstadoUsuario en mayúsculas que usa el resto de ms-identidad."""

    clienteId: UUID
    nombre: str
    apellidos: str
    documento: DocumentoSalida
    canal: str | None
    estado: str
    consentimiento: str

    @classmethod
    def desde(cls, usuario: Usuario, consentimiento: str) -> "ClienteSalida":
        return cls(
            clienteId=usuario.id,
            nombre=usuario.nombre,
            apellidos=usuario.apellidos,
            documento=DocumentoSalida(tipo=usuario.tipo_documento, numero=usuario.numero_documento),
            canal=usuario.canal,
            estado=usuario.estado.value.lower(),
            consentimiento=consentimiento,
        )


class ClientesSalida(BaseModel):
    clientes: list[ClienteSalida]


class ActualizarEstadoClienteEntrada(BaseModel):
    estado: str = Field(pattern="^(activo|inactivo)$")


class ActualizarRolUsuarioEntrada(BaseModel):
    rol: Literal["cliente", "asesor", "operador"]
