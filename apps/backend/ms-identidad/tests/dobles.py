from copy import deepcopy
from uuid import UUID

from app.domain.modelos import EventoDominio, Usuario
from app.ports.persistencia import TAMANO_PAGINA_CLIENTES, CuentaYaExiste


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.usuarios: dict[UUID, Usuario] = {}
        self.outbox: list[EventoDominio] = []
        self.chocar_en_proximo_commit: bool = False


class _Usuarios:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def obtener_por_email(self, email: str):
        vista = {**self._uow.almacen.usuarios, **self._uow.pendientes}
        return next(
            (deepcopy(u) for u in vista.values() if u.email.lower() == email.lower()),
            None,
        )

    async def obtener_por_documento(self, tipo_documento: str, numero_documento: str):
        vista = {**self._uow.almacen.usuarios, **self._uow.pendientes}
        return next(
            (
                deepcopy(u)
                for u in vista.values()
                if u.tipo_documento == tipo_documento and u.numero_documento == numero_documento
            ),
            None,
        )

    async def obtener_por_id(self, usuario_id: UUID):
        vista = {**self._uow.almacen.usuarios, **self._uow.pendientes}
        usuario = vista.get(usuario_id)
        return deepcopy(usuario) if usuario else None

    async def agregar(self, usuario: Usuario) -> None:
        self._uow.pendientes[usuario.id] = usuario

    async def actualizar(self, usuario: Usuario) -> None:
        self._uow.pendientes[usuario.id] = usuario

    async def listar_clientes(self, estado, q, ids, pagina):
        tamano = len(ids) if ids else TAMANO_PAGINA_CLIENTES
        vista = {**self._uow.almacen.usuarios, **self._uow.pendientes}
        usuarios = [usuario for usuario in vista.values() if usuario.rol == "cliente"]
        if estado is not None:
            usuarios = [usuario for usuario in usuarios if usuario.estado.value == estado]
        if q:
            aguja = q.casefold()
            usuarios = [
                usuario
                for usuario in usuarios
                if aguja in usuario.nombre.casefold()
                or aguja in usuario.apellidos.casefold()
                or aguja in usuario.email.casefold()
                or aguja in usuario.numero_documento.casefold()
            ]
        if ids:
            pedidos = set(ids)
            usuarios = [usuario for usuario in usuarios if usuario.id in pedidos]
        usuarios.sort(key=lambda usuario: (usuario.apellidos, usuario.nombre, usuario.id))
        inicio = (pagina - 1) * tamano
        pagina_filas = usuarios[inicio : inicio + tamano + 1]
        return [deepcopy(usuario) for usuario in pagina_filas[:tamano]], len(pagina_filas) > tamano

    async def listar_por_rol(self, rol: str):
        vista = {**self._uow.almacen.usuarios, **self._uow.pendientes}
        return [deepcopy(u) for u in vista.values() if u.rol == rol]


class _Outbox:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    async def agregar(self, evento: EventoDominio) -> None:
        self._uow.eventos_pendientes.append(evento)


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, Usuario] = {}
        self.eventos_pendientes: list[EventoDominio] = []
        self.usuarios = _Usuarios(self)
        self.outbox = _Outbox(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.pendientes.clear()
        self.eventos_pendientes.clear()

    async def confirmar(self):
        if self.almacen.chocar_en_proximo_commit:
            self.almacen.chocar_en_proximo_commit = False
            self.pendientes.clear()
            self.eventos_pendientes.clear()
            raise CuentaYaExiste
        self.almacen.usuarios.update(self.pendientes)
        self.almacen.outbox.extend(self.eventos_pendientes)
        self.pendientes.clear()
        self.eventos_pendientes.clear()
