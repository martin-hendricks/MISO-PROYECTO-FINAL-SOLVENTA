from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import Usuario


class CrearUsuarioEntrada(BaseModel):
    tipo_documento: str = Field(min_length=1, max_length=10)
    numero_documento: str = Field(min_length=1, max_length=50)
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=72)


class AutenticarEntrada(BaseModel):
    email: str = Field(min_length=1, max_length=254)
    password: str = Field(min_length=1, max_length=72)


class UsuarioSalida(BaseModel):
    usuario_id: UUID
    tipo_documento: str
    numero_documento: str
    email: str
    estado: str

    @classmethod
    def desde(cls, usuario: Usuario) -> "UsuarioSalida":
        return cls(
            usuario_id=usuario.id,
            tipo_documento=usuario.tipo_documento,
            numero_documento=usuario.numero_documento,
            email=usuario.email,
            estado=usuario.estado.value,
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
