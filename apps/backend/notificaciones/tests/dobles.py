from copy import deepcopy
from collections.abc import Iterable
from uuid import UUID

from app.domain.errores import ServicioExternoNoDisponible
from app.domain.modelos import Difusion, DispositivoPush, Notificacion
from app.ports.persistencia import DispositivoDuplicado, NotificacionDuplicada
from app.ports.push import EstadoEnvio, ResultadoEnvio


class AlmacenEnMemoria:
    def __init__(self) -> None:
        self.notificaciones: dict[UUID, Notificacion] = {}
        self.dispositivos: dict[UUID, DispositivoPush] = {}
        self.difusiones: dict[UUID, Difusion] = {}
        self.eventos_consumidos: set[UUID] = set()
        self.chocar_notificacion: Notificacion | None = None
        self.chocar_dispositivo: DispositivoPush | None = None


class _Notificaciones:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, Notificacion]:
        return {**self._uow.almacen.notificaciones, **self._uow.notificaciones_pendientes}

    async def obtener(self, notificacion_id):
        notificacion = self._vista().get(notificacion_id)
        return deepcopy(notificacion) if notificacion else None

    async def obtener_por_evento_canal(self, evento_origen_id, canal):
        return next(
            (
                deepcopy(n)
                for n in self._vista().values()
                if n.evento_origen_id == evento_origen_id and n.canal == canal
            ),
            None,
        )

    async def listar(self, usuario_id, limite, antes_de=None):
        notificaciones = sorted(
            (
                n
                for n in self._vista().values()
                if n.usuario_id == usuario_id
                and (antes_de is None or n.creada_en < antes_de)
            ),
            key=lambda n: n.creada_en,
            reverse=True,
        )
        return [deepcopy(n) for n in notificaciones[:limite]]

    async def listar_pendientes_push(self, usuario_id=None, limite=100):
        pendientes = sorted(
            (
                n
                for n in self._vista().values()
                if n.estado == "pendiente"
                and n.canal == "push"
                and (usuario_id is None or n.usuario_id == usuario_id)
            ),
            key=lambda n: n.creada_en,
        )
        return [deepcopy(n) for n in pendientes[:limite]]

    async def agregar(self, notificacion):
        self._uow.notificaciones_pendientes[notificacion.notificacion_id] = notificacion

    async def actualizar(self, notificacion):
        self._uow.notificaciones_pendientes[notificacion.notificacion_id] = notificacion


class _Dispositivos:
    def __init__(self, uow: "UnidadDeTrabajoEnMemoria") -> None:
        self._uow = uow

    def _vista(self) -> dict[UUID, DispositivoPush]:
        return {**self._uow.almacen.dispositivos, **self._uow.dispositivos_pendientes}

    async def obtener(self, dispositivo_id):
        dispositivo = self._vista().get(dispositivo_id)
        return deepcopy(dispositivo) if dispositivo else None

    async def obtener_por_usuario_token(self, usuario_id, token):
        return next(
            (
                deepcopy(d)
                for d in self._vista().values()
                if d.usuario_id == usuario_id and d.token == token
            ),
            None,
        )

    async def listar_activos(self, usuario_id):
        return [
            deepcopy(d)
            for d in self._vista().values()
            if d.usuario_id == usuario_id and d.activo
        ]

    async def agregar(self, dispositivo):
        self._uow.dispositivos_pendientes[dispositivo.dispositivo_id] = dispositivo

    async def actualizar(self, dispositivo):
        self._uow.dispositivos_pendientes[dispositivo.dispositivo_id] = dispositivo

    async def contar_activos(self, usuario_ids=None):
        conteo: dict[UUID, int] = {}
        for dispositivo in self._vista().values():
            if not dispositivo.activo:
                continue
            if usuario_ids is not None and dispositivo.usuario_id not in usuario_ids:
                continue
            conteo[dispositivo.usuario_id] = conteo.get(dispositivo.usuario_id, 0) + 1
        return sorted(conteo.items(), key=lambda par: str(par[0]))

    async def desactivar_de_usuario(self, usuario_id):
        from datetime import UTC, datetime

        for dispositivo in list(self._vista().values()):
            if dispositivo.usuario_id == usuario_id and dispositivo.activo:
                dispositivo.desactivar(datetime.now(UTC))
                self._uow.dispositivos_pendientes[dispositivo.dispositivo_id] = dispositivo


class UnidadDeTrabajoEnMemoria:
    def __init__(self, almacen: AlmacenEnMemoria) -> None:
        self.almacen = almacen
        self.notificaciones_pendientes: dict[UUID, Notificacion] = {}
        self.dispositivos_pendientes: dict[UUID, DispositivoPush] = {}
        self.notificaciones = _Notificaciones(self)
        self.dispositivos = _Dispositivos(self)
        self.difusiones = _Difusiones(self)
        self.eventos = _Eventos(self)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.notificaciones_pendientes.clear()
        self.dispositivos_pendientes.clear()

    async def confirmar(self):
        if self.almacen.chocar_notificacion is not None:
            ganadora = self.almacen.chocar_notificacion
            self.almacen.chocar_notificacion = None
            self.almacen.notificaciones[ganadora.notificacion_id] = ganadora
            raise NotificacionDuplicada
        if self.almacen.chocar_dispositivo is not None:
            ganador = self.almacen.chocar_dispositivo
            self.almacen.chocar_dispositivo = None
            self.almacen.dispositivos[ganador.dispositivo_id] = ganador
            raise DispositivoDuplicado
        self.almacen.notificaciones.update(self.notificaciones_pendientes)
        self.almacen.dispositivos.update(self.dispositivos_pendientes)
        self.notificaciones_pendientes.clear()
        self.dispositivos_pendientes.clear()


class PushDoble:
    def __init__(self, fallar: bool = False) -> None:
        self.fallar = fallar
        self.llamadas: list[tuple[list[UUID], UUID]] = []

    async def enviar(self, dispositivo: DispositivoPush, notificacion: Notificacion) -> str:
        if self.fallar:
            raise ServicioExternoNoDisponible("push doble no disponible")
        return f"doble-{notificacion.notificacion_id}-{dispositivo.dispositivo_id}"

    async def enviar_a_usuario(
        self, dispositivos: list[DispositivoPush], notificacion: Notificacion
    ) -> list[ResultadoEnvio]:
        self.llamadas.append(
            ([d.dispositivo_id for d in dispositivos], notificacion.notificacion_id)
        )
        if self.fallar:
            raise ServicioExternoNoDisponible("push doble no disponible")
        invalidos = getattr(self, "tokens_invalidos", set())
        resultados = []
        for dispositivo in dispositivos:
            if dispositivo.token in invalidos:
                resultados.append(
                    ResultadoEnvio(dispositivo.dispositivo_id, EstadoEnvio.TOKEN_INVALIDO.value)
                )
                continue
            resultados.append(
                ResultadoEnvio(
                    dispositivo.dispositivo_id,
                    EstadoEnvio.ENVIADO.value,
                    await self.enviar(dispositivo, notificacion),
                )
            )
        return resultados


class _Difusiones:
    def __init__(self, uow: UnidadDeTrabajoEnMemoria) -> None:
        self._uow = uow

    async def agregar(self, difusion: Difusion) -> None:
        self._uow.almacen.difusiones[difusion.difusion_id] = difusion

    async def actualizar_totales(self, difusion_id, enviadas, fallidas, sin_dispositivo) -> None:
        difusion = self._uow.almacen.difusiones[difusion_id]
        difusion.registrar_totales(enviadas, fallidas, sin_dispositivo)

    async def listar(self, limite, antes_de=None):
        filas = [
            d
            for d in self._uow.almacen.difusiones.values()
            if antes_de is None or d.creada_en < antes_de
        ]
        filas.sort(key=lambda d: d.creada_en, reverse=True)
        return filas[:limite]


class _Eventos:
    def __init__(self, uow: UnidadDeTrabajoEnMemoria) -> None:
        self._uow = uow

    async def consumir(self, evento_id, tipo) -> bool:
        if evento_id in self._uow.almacen.eventos_consumidos:
            return False
        self._uow.almacen.eventos_consumidos.add(evento_id)
        return True


def sembrar_notificaciones(almacen: AlmacenEnMemoria, notificaciones: Iterable[Notificacion]) -> None:
    for notificacion in notificaciones:
        almacen.notificaciones[notificacion.notificacion_id] = notificacion
