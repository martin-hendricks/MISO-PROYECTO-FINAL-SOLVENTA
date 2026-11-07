from __future__ import annotations

from app.domain.errores import ServicioExternoNoDisponible
from app.domain.modelos import DispositivoPush, Notificacion


class PushStub:
    """Adaptador determinista de push para desarrollo y pruebas.

    No habla con FCM ni APNs: no hay credenciales en el repositorio. El adaptador real
    se conecta sustituyendo la fábrica en `main.py` (ver README del servicio).
    """

    def __init__(self, fallar: bool = False) -> None:
        self._fallar = fallar

    async def enviar(self, dispositivo: DispositivoPush, notificacion: Notificacion) -> str:
        if self._fallar:
            raise ServicioExternoNoDisponible("Proveedor de push no disponible (stub)")
        return f"stub-{notificacion.notificacion_id}"

    async def enviar_a_usuario(
        self, dispositivos: list[DispositivoPush], notificacion: Notificacion
    ) -> list[str]:
        return [await self.enviar(dispositivo, notificacion) for dispositivo in dispositivos]
