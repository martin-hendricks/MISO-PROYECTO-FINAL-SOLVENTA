from copy import deepcopy
from uuid import UUID

from app.domain.modelos import Usuario
from app.ports.persistencia import CuentaYaExiste


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.usuarios: dict[UUID, Usuario] = {}
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

    async def agregar(self, usuario: Usuario) -> None:
        self._uow.pendientes[usuario.id] = usuario


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, Usuario] = {}
        self.usuarios = _Usuarios(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.pendientes.clear()

    async def confirmar(self):
        if self.almacen.chocar_en_proximo_commit:
            self.almacen.chocar_en_proximo_commit = False
            self.pendientes.clear()
            raise CuentaYaExiste
        self.almacen.usuarios.update(self.pendientes)
        self.pendientes.clear()
