from __future__ import annotations

from app.domain.errores import NoEncontrado
from app.domain.modelos import EstadoUsuario, Usuario
from app.ports.consentimiento import ConsultaConsentimiento
from app.ports.perfilamiento import ConsultaPerfilamiento
from app.ports.persistencia import FabricaUnidadDeTrabajo

ROL_CLIENTE = "cliente"

# Valores del campo "consentimiento" que ve el back-office (HU-141).
HIPOTECARIO_PENDIENTE = "hipotecario_pendiente"
HABEAS_DATA = "habeas_data"
REVOCADO = "revocado"


async def listar_clientes(
    uow: FabricaUnidadDeTrabajo,
    consentimiento: ConsultaConsentimiento,
    perfilamiento: ConsultaPerfilamiento,
) -> list[tuple[Usuario, str]]:
    """Listado de clientes del back-office (HU-141): todo usuario con
    rol="cliente", cada uno con su campo `consentimiento` ya resuelto.

    Devuelve pares (Usuario, consentimiento) en vez de mutar el dominio:
    `consentimiento` no es un atributo de Usuario, es un dato compuesto que
    solo existe en la vista del back-office (ver resolver_consentimiento)."""
    async with uow() as tx:
        clientes = await tx.usuarios.listar_por_rol(ROL_CLIENTE)

    return [(cliente, await resolver_consentimiento(cliente.id, consentimiento, perfilamiento)) for cliente in clientes]


async def obtener_cliente(
    uow: FabricaUnidadDeTrabajo,
    usuario_id,
    consentimiento: ConsultaConsentimiento,
    perfilamiento: ConsultaPerfilamiento,
) -> tuple[Usuario, str]:
    """Ficha de un cliente individual (HU-141). 404 si no existe o si existe
    pero no tiene rol="cliente" -- el back-office no "ficha" asesores u
    operadores por esta vía."""
    async with uow() as tx:
        usuario = await tx.usuarios.obtener_por_id(usuario_id)
    if usuario is None or usuario.rol != ROL_CLIENTE:
        raise NoEncontrado("Cliente no encontrado")

    return usuario, await resolver_consentimiento(usuario.id, consentimiento, perfilamiento)


async def actualizar_estado_cliente(
    uow: FabricaUnidadDeTrabajo,
    usuario_id,
    nuevo_estado: EstadoUsuario,
) -> Usuario:
    """Activa/desactiva un cliente desde el back-office (HU-141). Mismo
    candado que obtener_cliente: solo opera sobre usuarios con
    rol="cliente"."""
    async with uow() as tx:
        usuario = await tx.usuarios.obtener_por_id(usuario_id)
        if usuario is None or usuario.rol != ROL_CLIENTE:
            raise NoEncontrado("Cliente no encontrado")
        usuario.cambiar_estado(nuevo_estado)
        await tx.usuarios.actualizar(usuario)
        await tx.confirmar()
    return usuario


async def resolver_consentimiento(
    cliente_id,
    consentimiento: ConsultaConsentimiento,
    perfilamiento: ConsultaPerfilamiento,
) -> str:
    """Combina dos servicios externos en un único campo `consentimiento`
    (HU-141), en este orden de prioridad:

    1. Si ms-perfilamiento tiene una Originacion abierta (cerrada_en IS
       NULL) para este cliente -> "hipotecario_pendiente". Una originación
       en curso importa más que el estado del habeas data: el back-office
       necesita ver primero que hay un crédito hipotecario en trámite.
    2. Si no hay originación abierta, y ms-consentimiento confirma habeas
       data vigente -> "habeas_data".
    3. En cualquier otro caso (sin habeas data vigente, o ms-consentimiento
       no distingue "nunca otorgado" de "revocado" en su 404) -> "revocado".

    Esta función nunca propaga un error de los adaptadores HTTP: ambos
    puertos ya degradan a False internamente si el servicio externo no
    responde (ver infrastructure/consentimiento_http.py y
    perfilamiento_http.py) -- aquí solo se combina el resultado."""
    cliente_id_str = str(cliente_id)

    if await perfilamiento.tiene_originacion_pendiente(cliente_id_str):
        return HIPOTECARIO_PENDIENTE
    if await consentimiento.vigente(cliente_id_str):
        return HABEAS_DATA
    return REVOCADO
