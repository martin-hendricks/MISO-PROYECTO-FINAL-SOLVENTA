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
        self,
        *,
        tipo_documento: str,
        numero_documento: str,
        email: str,
        password: str,
        nombre: str = "",
        apellidos: str = "",
        ingresos_mensuales: str | None = None,
        gastos_mensuales: str | None = None,
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
                "nombre": nombre,
                "apellidos": apellidos,
                "ingresos_mensuales": None if ingresos_mensuales is None else str(ingresos_mensuales),
                "gastos_mensuales": None if gastos_mensuales is None else str(gastos_mensuales),
            },
        )

    async def obtener(self, usuario_id: str) -> dict[str, Any]:
        return await self._pedir("GET", f"/v1/usuarios/{usuario_id}")

    async def actualizar_perfil(self, usuario_id: str, *, nombre: str, apellidos: str) -> dict[str, Any]:
        return await self._pedir(
            "PATCH",
            f"/v1/usuarios/{usuario_id}/perfil",
            json={"nombre": nombre, "apellidos": apellidos},
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

    async def listar_clientes(self) -> list[dict[str, Any]]:
        """GET /v1/clientes (HU-141): back-office únicamente -- ms-identidad
        ya exige rol asesor/operador, bff-web solo reenvía el token."""
        return (await self._pedir("GET", "/v1/clientes"))["clientes"]

    async def actualizar_estado_cliente(self, usuario_id: str, estado: str) -> dict[str, Any]:
        """PATCH /v1/clientes/{usuario_id}/estado (HU-141): activa/desactiva
        un cliente desde el back-office."""
        return await self._pedir(
            "PATCH",
            f"/v1/clientes/{usuario_id}/estado",
            json={"estado": estado},
        )
