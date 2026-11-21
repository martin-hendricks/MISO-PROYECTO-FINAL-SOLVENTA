from typing import Protocol

from app.domain.evento import EventoTelemetria


class PublicadorSaturado(Exception):
    """Contrapresión: la réplica ya tiene el máximo de publicaciones en vuelo. El
    proveedor debe reintentar más tarde (429 + Retry-After)."""


class PublicadorNoDisponible(Exception):
    """El tópico no confirmó la escritura (broker caído o lento). El evento NO quedó
    aceptado: el proveedor debe reintentar (503 + Retry-After)."""


class PublicadorEventos(Protocol):
    async def publicar(self, evento: EventoTelemetria) -> None:
        """Retorna solo cuando el tópico confirmó la escritura (acks=all). Si no, lanza
        PublicadorSaturado o PublicadorNoDisponible: nunca hay 202 sin evento persistido."""
        ...

    def listo(self) -> bool: ...
