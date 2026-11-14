from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.application import casos_uso
from app.dependencies import obtener_uow, obtener_verificador_kyc
from app.ports.kyc import VerificadorKYC
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import (
    Llamante,
    LlamanteDep,
    alcance,
    exigir_backoffice,
    exigir_busqueda_por_documento,
    exigir_operador,
)

from .schemas import (
    AutenticarEntrada,
    CrearUsuarioEntrada,
    EditarClienteEntrada,
    ErrorSalida,
    EstadoEntrada,
    ListaUsuariosSalida,
    PerfilEntrada,
    PruebaDeVidaEntrada,
    UsuarioPorDocumentoSalida,
    UsuarioSalida,
)

router = APIRouter(prefix="/v1/usuarios", tags=["usuarios"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]
Kyc = Annotated[VerificadorKYC, Depends(obtener_verificador_kyc)]
ERRORES = {
    401: {"model": ErrorSalida},
    409: {"model": ErrorSalida},
    422: {"model": ErrorSalida},
    503: {"model": ErrorSalida},
}


@router.post("", response_model=UsuarioSalida, status_code=status.HTTP_201_CREATED, responses=ERRORES)
async def crear(entrada: CrearUsuarioEntrada, uow: Uow, kyc: Kyc):
    """Alta de cuenta (SOLV-215). 409 si el correo o el documento ya existen; 422 si el KYC
    rechaza el documento y 503 si el proveedor KYC no responde (HU-88)."""
    usuario = await casos_uso.crear_usuario(
        uow,
        kyc,
        tipo_documento=entrada.tipo_documento,
        numero_documento=entrada.numero_documento,
        email=entrada.email,
        password_plano=entrada.password,
        nombre=entrada.nombre,
        apellidos=entrada.apellidos,
        ingresos_mensuales=entrada.ingresos_mensuales,
        gastos_mensuales=entrada.gastos_mensuales,
        prueba_de_vida=entrada.prueba_de_vida,
        canal=entrada.canal,
    )
    return UsuarioSalida.desde(usuario)


@router.get("", response_model=ListaUsuariosSalida, responses=ERRORES)
async def listar(
    uow: Uow,
    _llamante: Annotated[Llamante, Depends(exigir_backoffice)],
    rol: Annotated[str, Query()],
    estado: Annotated[str | None, Query()] = None,
    q: Annotated[str | None, Query()] = None,
    ids: Annotated[list[UUID] | None, Query()] = None,
    pagina: Annotated[int, Query(ge=1)] = 1,
):
    """Lista cuentas con rol cliente. Operador y asesor; el cliente recibe 403."""
    usuarios, hay_mas = await casos_uso.listar_clientes(
        uow, rol=rol, estado=estado, q=q, ids=ids, pagina=pagina
    )
    return ListaUsuariosSalida(
        usuarios=[UsuarioSalida.desde(usuario) for usuario in usuarios],
        pagina=pagina,
        hay_mas=hay_mas,
    )


@router.post("/autenticacion", response_model=UsuarioSalida, responses=ERRORES)
async def autenticacion(entrada: AutenticarEntrada, uow: Uow):
    """Valida credenciales (SOLV-215). 401 indistinguible si el correo no
    existe o si la contraseña no coincide. No emite JWT: eso es
    responsabilidad de bff-web (issue_pair) una vez recibe este 200."""
    usuario = await casos_uso.autenticar_usuario(uow, email=entrada.email, password_plano=entrada.password)
    return UsuarioSalida.desde(usuario)


@router.get("/documento", response_model=UsuarioPorDocumentoSalida, responses=ERRORES)
async def buscar_por_documento(
    uow: Uow,
    llamante: LlamanteDep,
    tipo_documento: Annotated[str, Query(min_length=1, max_length=10)],
    numero_documento: Annotated[str, Query(min_length=1, max_length=50)],
):
    """Resuelve el usuario de un documento para un socio o el back-office. Solo
    devuelve el usuario_id: el resto de la cuenta no sale de este endpoint."""
    exigir_busqueda_por_documento(llamante)
    usuario = await casos_uso.buscar_por_documento(uow, tipo_documento, numero_documento)
    return UsuarioPorDocumentoSalida(usuario_id=usuario.id)


@router.get("/{usuario_id}", response_model=UsuarioSalida, responses=ERRORES)
async def consultar(usuario_id: UUID, uow: Uow, llamante: LlamanteDep):
    alcance(llamante, usuario_id)
    if llamante.rol == "cliente" and llamante.uid != usuario_id:
        from app.domain.errores import NoEncontrado

        raise NoEncontrado()
    return UsuarioSalida.desde(await casos_uso.consultar_usuario(uow, usuario_id))


@router.patch("/{usuario_id}/prueba-de-vida", response_model=UsuarioSalida, responses=ERRORES)
async def registrar_prueba_de_vida(
    usuario_id: UUID, entrada: PruebaDeVidaEntrada, uow: Uow, llamante: LlamanteDep
):
    if llamante.rol != "cliente" or llamante.uid != usuario_id:
        from app.domain.errores import NoEncontrado

        raise NoEncontrado()
    usuario = await casos_uso.registrar_prueba_de_vida(uow, usuario_id, valor=entrada.prueba_de_vida)
    return UsuarioSalida.desde(usuario)


@router.patch("/{usuario_id}/perfil", response_model=UsuarioSalida, responses=ERRORES)
async def actualizar_perfil(usuario_id: UUID, entrada: PerfilEntrada, uow: Uow, llamante: LlamanteDep):
    if llamante.rol != "cliente" or llamante.uid != usuario_id:
        from app.domain.errores import NoEncontrado

        raise NoEncontrado()
    usuario = await casos_uso.actualizar_perfil(
        uow, usuario_id, nombre=entrada.nombre, apellidos=entrada.apellidos
    )
    return UsuarioSalida.desde(usuario)


@router.patch("/{usuario_id}", response_model=UsuarioSalida, responses=ERRORES)
async def editar(
    usuario_id: UUID,
    entrada: EditarClienteEntrada,
    uow: Uow,
    _llamante: Annotated[Llamante, Depends(exigir_operador)],
):
    usuario = await casos_uso.editar_cliente(
        uow, usuario_id, nombre=entrada.nombre, apellidos=entrada.apellidos, email=entrada.email
    )
    return UsuarioSalida.desde(usuario)


@router.post("/{usuario_id}/estado", response_model=UsuarioSalida, responses=ERRORES)
async def cambiar_estado(
    usuario_id: UUID,
    entrada: EstadoEntrada,
    uow: Uow,
    _llamante: Annotated[Llamante, Depends(exigir_operador)],
):
    usuario = await casos_uso.cambiar_estado_cliente(uow, usuario_id, entrada.estado)
    return UsuarioSalida.desde(usuario)
