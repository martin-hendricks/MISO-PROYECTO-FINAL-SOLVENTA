from __future__ import annotations

from typing import Any

from .base import ClienteServicio


class ClienteMsIdentidad(ClienteServicio):
    """Cliente de ms-identidad: alta de cuenta y validación de credenciales.

    ms-identidad nunca emite JWT -- eso sigue siendo responsabilidad de
    bff-web (ver app/dependencies.py, issue_pair). Este cliente solo
    confirma identidad; routers/registro.py y routers/sesion.py son quienes
    deciden qué hacer con la confirmación (emitir tokens, asignar rol, etc).
    """

    nombre = "ms-identidad"

    async def crear_usuario(
        self, *, tipo_documento: str, numero_documento: str, email: str, password: str
    ) -> dict[str, Any]:
        """POST /v1/usuarios. ms-identidad responde 409 (RechazoDelNucleo)
        si el correo o el documento ya existen -- el router lo propaga como
        un rechazo de negocio, no como un error de servidor."""
        return await self._pedir(
            "POST",
            "/v1/usuarios",
            json={
                "tipo_documento": tipo_documento,
                "numero_documento": numero_documento,
                "email": email,
                "password": password,
            },
        )

    async def autenticar(self, *, email: str, password: str) -> dict[str, Any]:
        """POST /v1/usuarios/autenticacion. ms-identidad responde 401
        (RechazoDelNucleo) si el correo no existe o la contraseña no
        coincide -- mismo código/mensaje en ambos casos, no se revela cuál."""
        return await self._pedir(
            "POST",
            "/v1/usuarios/autenticacion",
            json={"email": email, "password": password},
        )
