from __future__ import annotations

from uuid import UUID

from app.domain.errores import (
    Conflicto,
    CuentaDuplicada,
    IdentidadNoVerificada,
    NoEncontrado,
    ReglaDeNegocioViolada,
)
from app.domain.modelos import EstadoUsuario, Usuario, autenticar
from app.ports.kyc import VerificadorKYC
from app.ports.persistencia import CuentaYaExiste, FabricaUnidadDeTrabajo


async def crear_usuario(
    uow: FabricaUnidadDeTrabajo,
    kyc: VerificadorKYC,
    *,
    tipo_documento: str,
    numero_documento: str,
    email: str,
    password_plano: str,
    nombre: str = "",
    apellidos: str = "",
    ingresos_mensuales=None,
    gastos_mensuales=None,
    canal: str | None = None,
) -> Usuario:
    """Alta de cuenta (SOLV-215). La verificación previa de duplicados es
    una optimización para responder rápido en el caso común; la garantía
    real de unicidad vive en los índices únicos de la base (uq_usuario_email,
    uq_usuario_documento) y se traduce aquí vía CuentaYaExiste, por si dos
    altas concurrentes pasan la verificación previa a la vez.

    El KYC (HU-88) se consulta antes de abrir la transacción, para no retenerla
    mientras responde el proveedor.

    `canal` (HU-141) es opcional: el alta desde el registro propio del canal
    web/app ya lo conoce (quién llama); el alta desde el back-office también
    lo fija explícitamente (ver bff-web/routers/asesor.py)."""
    usuario = Usuario.crear(
        tipo_documento=tipo_documento,
        numero_documento=numero_documento,
        email=email,
        password_plano=password_plano,
        nombre=nombre,
        apellidos=apellidos,
        ingresos_mensuales=ingresos_mensuales,
        gastos_mensuales=gastos_mensuales,
        canal=canal,
    )
    if not await kyc.verificar(usuario.tipo_documento, usuario.numero_documento):
        raise IdentidadNoVerificada()

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


async def consultar_usuario(uow: FabricaUnidadDeTrabajo, usuario_id) -> Usuario:
    async with uow() as tx:
        usuario = await tx.usuarios.obtener_por_id(usuario_id)
    if usuario is None:
        raise NoEncontrado()
    return usuario


async def actualizar_perfil(
    uow: FabricaUnidadDeTrabajo, usuario_id, *, nombre: str, apellidos: str
) -> Usuario:
    async with uow() as tx:
        usuario = await tx.usuarios.obtener_por_id(usuario_id)
        if usuario is None:
            raise NoEncontrado()
        usuario.actualizar_perfil(nombre=nombre, apellidos=apellidos)
        await tx.usuarios.actualizar(usuario)
        await tx.confirmar()
    return usuario


def _validar_listado(
    *, rol: str, estado: str | None, q: str | None, ids: list[UUID] | None, pagina: int
) -> None:
    if rol != "cliente":
        raise ReglaDeNegocioViolada("rol_no_soportado", "Solo se puede listar el rol cliente")
    if q is not None and not 2 <= len(q) <= 80:
        codigo = "consulta_corta" if len(q) < 2 else "consulta_larga"
        raise ReglaDeNegocioViolada(codigo, "La búsqueda debe tener entre 2 y 80 caracteres")
    if ids is not None and len(ids) > 50:
        raise ReglaDeNegocioViolada("ids_largos", "No se pueden consultar más de 50 identificadores")
    if estado is not None and estado not in (EstadoUsuario.ACTIVO.value, EstadoUsuario.INACTIVO.value):
        raise ReglaDeNegocioViolada("estado_invalido", "El estado debe ser ACTIVO o INACTIVO")
    if pagina < 1:
        raise ReglaDeNegocioViolada("pagina_invalida", "La página empieza en 1")


async def listar_clientes(
    uow: FabricaUnidadDeTrabajo,
    *,
    rol: str,
    estado: str | None,
    q: str | None,
    ids: list[UUID] | None,
    pagina: int,
) -> tuple[list[Usuario], bool]:
    _validar_listado(rol=rol, estado=estado, q=q, ids=ids, pagina=pagina)
    async with uow() as tx:
        return await tx.usuarios.listar_clientes(estado, q, ids, pagina)


def _exigir_cliente(usuario: Usuario | None) -> Usuario:
    if usuario is None or usuario.rol != "cliente":
        raise NoEncontrado()
    return usuario


async def editar_cliente(
    uow: FabricaUnidadDeTrabajo,
    usuario_id: UUID,
    *,
    nombre: str,
    apellidos: str,
    email: str,
) -> Usuario:
    async with uow() as tx:
        usuario = _exigir_cliente(await tx.usuarios.obtener_por_id(usuario_id))
        usuario.editar(nombre=nombre, apellidos=apellidos, email=email)
        otro = await tx.usuarios.obtener_por_email(usuario.email)
        if otro is not None and otro.id != usuario.id:
            raise Conflicto("El correo ya está en uso")
        await tx.usuarios.actualizar(usuario)
        try:
            await tx.confirmar()
        except CuentaYaExiste as exc:
            raise Conflicto("El correo ya está en uso") from exc
    return usuario


async def cambiar_estado_cliente(uow: FabricaUnidadDeTrabajo, usuario_id: UUID, estado: str) -> Usuario:
    if estado not in (EstadoUsuario.ACTIVO.value, EstadoUsuario.INACTIVO.value):
        raise ReglaDeNegocioViolada("estado_invalido", "El estado debe ser ACTIVO o INACTIVO")
    async with uow() as tx:
        usuario = _exigir_cliente(await tx.usuarios.obtener_por_id(usuario_id))
        evento = usuario.inactivar() if estado == EstadoUsuario.INACTIVO.value else usuario.activar()
        if evento is not None:
            await tx.usuarios.actualizar(usuario)
            await tx.outbox.agregar(evento)
        await tx.confirmar()
    return usuario


async def buscar_por_documento(uow: FabricaUnidadDeTrabajo, tipo_documento: str, numero_documento: str) -> Usuario:
    async with uow() as tx:
        usuario = await tx.usuarios.obtener_por_documento(tipo_documento.strip().upper(), numero_documento.strip())
    if usuario is None:
        raise NoEncontrado()
    return usuario
