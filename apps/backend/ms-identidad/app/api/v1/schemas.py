from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import Usuario


class CrearUsuarioEntrada(BaseModel):
    tipo_documento: str = Field(min_length=1, max_length=10)
    numero_documento: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=72)
    nombre: str = ""
    apellidos: str = ""
    ingresos_mensuales: Decimal | None = Field(default=None, gt=0)
    gastos_mensuales: Decimal | None = Field(default=None, ge=0)
    prueba_de_vida: Literal["ok", "no"] = "no"


class PruebaDeVidaEntrada(BaseModel):
    prueba_de_vida: Literal["ok", "no"]


class PerfilEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    apellidos: str = Field(min_length=1, max_length=80)


class EditarClienteEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=80)
    apellidos: str = Field(min_length=1, max_length=80)
    email: str = Field(min_length=3, max_length=254)


class EstadoEntrada(BaseModel):
    estado: Literal["ACTIVO", "INACTIVO"]


class AutenticarEntrada(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=72)


class UsuarioSalida(BaseModel):
    usuario_id: UUID
    tipo_documento: str
    numero_documento: str
    email: str
    estado: str
    nombre: str = ""
    apellidos: str = ""
    ingresos_mensuales: Decimal | None = None
    gastos_mensuales: Decimal | None = None
    rol: str = "cliente"
    prueba_de_vida: str = "no"

    @classmethod
    def desde(cls, usuario: Usuario) -> "UsuarioSalida":
        return cls(
            usuario_id=usuario.id,
            tipo_documento=usuario.tipo_documento,
            numero_documento=usuario.numero_documento,
            email=usuario.email,
            estado=usuario.estado.value,
            nombre=usuario.nombre,
            apellidos=usuario.apellidos,
            ingresos_mensuales=usuario.ingresos_mensuales,
            gastos_mensuales=usuario.gastos_mensuales,
            rol=usuario.rol,
            prueba_de_vida=usuario.prueba_de_vida,
        )


class ListaUsuariosSalida(BaseModel):
    usuarios: list[UsuarioSalida]
    pagina: int
    hay_mas: bool


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
