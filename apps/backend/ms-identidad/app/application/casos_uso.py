from __future__ import annotations

from app.domain.errores import CuentaDuplicada
from app.domain.modelos import Usuario, autenticar
from app.ports.persistencia import CuentaYaExiste, FabricaUnidadDeTrabajo


async def crear_usuario(
    uow: FabricaUnidadDeTrabajo,
    *,
    tipo_documento: str,
    numero_documento: str,
    email: str,
    password_plano: str,
) -> Usuario:
    """Alta de cuenta (SOLV-215). La verificación previa de duplicados es
    una optimización para responder rápido en el caso común; la garantía
    real de unicidad vive en los índices únicos de la base (uq_usuario_email,
    uq_usuario_documento) y se traduce aquí vía CuentaYaExiste, por si dos
    altas concurrentes pasan la verificación previa a la vez."""
    usuario = Usuario.crear(
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
        email=email,
        password_plano=password_plano,
    )

    async with uow() as tx:
        if await tx.usuarios.obtener_por_email(usuario.email) is not None:
            raise CuentaDuplicada()
        if await tx.usuarios.obtener_por_documento(usuario.tipo_documento, usuario.numero_documento) is not None:
            raise CuentaDuplicada()

        await tx.usuarios.agregar(usuario)
        try:
            await tx.confirmar()
        except CuentaYaExiste as exc:
            raise CuentaDuplicada() from exc

    return usuario


async def autenticar_usuario(uow: FabricaUnidadDeTrabajo, *, email: str, password_plano: str) -> Usuario:
    """Login real (SOLV-215): ms-identidad solo confirma identidad, nunca
    emite JWT (eso sigue siendo responsabilidad de bff-web)."""
    async with uow() as tx:
        usuario = await tx.usuarios.obtener_por_email(email.strip().lower())

    return autenticar(usuario, password_plano)
