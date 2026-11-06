from __future__ import annotations

from typing import Protocol


class ErrorAlmacenEvidencias(Exception):
    """El almacén de objetos (S3) no respondió o rechazó la operación."""


class AlmacenEvidencias(Protocol):
    """Puerto del almacén de evidencia (N6). La implementación real es S3 (LocalStack en local);
    las pruebas usan un doble en memoria. Cambiar de proveedor no toca application/."""

    @property
    def bucket(self) -> str: ...

    async def guardar(self, clave: str, contenido: bytes, content_type: str) -> None: ...

    async def url_lectura(self, clave: str, expira_segundos: int = 300) -> str:
        """URL firmada y temporal: la evidencia es privada y nunca se expone una URL fija."""
        ...
