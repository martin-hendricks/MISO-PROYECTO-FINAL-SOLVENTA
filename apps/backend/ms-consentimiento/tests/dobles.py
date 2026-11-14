from copy import deepcopy
from uuid import UUID

from app.domain.modelos import Consentimiento


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.consentimientos: dict[UUID, Consentimiento] = {}


class _RepositorioConsentimientos:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, Consentimiento]:
        return {**self._uow.almacen.consentimientos, **self._uow.pendientes}

    async def obtener_vigente(self, cliente_id: str) -> Consentimiento | None:
        candidatos = [
            c for c in self._vista().values() if c.cliente_id == cliente_id and c.revocado_en is None
        ]
        candidatos.sort(key=lambda c: c.otorgado_en, reverse=True)
        return deepcopy(candidatos[0]) if candidatos else None

    async def obtener_por_id(self, consentimiento_id: UUID) -> Consentimiento | None:
        c = self._vista().get(consentimiento_id)
        return deepcopy(c) if c else None

    async def agregar(self, consentimiento: Consentimiento) -> None:
        self._uow.pendientes[consentimiento.id] = consentimiento

    async def actualizar(self, consentimiento: Consentimiento) -> None:
        self._uow.pendientes[consentimiento.id] = consentimiento


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.pendientes: dict[UUID, Consentimiento] = {}
        self.consentimientos = _RepositorioConsentimientos(self)

    async def __aenter__(self) -> "UnidadDeTrabajoEnMemoria":
        return self

    async def __aexit__(self, *exc: object) -> None:
        self.pendientes.clear()

    async def confirmar(self) -> None:
        self.almacen.consentimientos.update(self.pendientes)
        self.pendientes.clear()
