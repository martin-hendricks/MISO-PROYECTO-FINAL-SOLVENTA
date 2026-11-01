from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from uuid import UUID

import httpx

from app.ports.riesgo import AdaptadorPerfilRiesgo


class AdaptadorPerfilRiesgoPerfilamiento:
    """IPerfilRiesgo real (diagrama de componentes: Cotización requiere, Perfilamiento
    provee). Lee el `factor_ajuste` de la última oferta que ms-perfilamiento armó para el
    cliente, así la prima de vida crediticia sale del mismo perfil que el cliente vio
    explicado. Cualquier fallo -- sin consentimiento, sin oferta, servicio caído o un
    factor inválido -- se lanza tal cual: el caso de uso aplica timeout y valor de
    respaldo (ver ports/riesgo.py), este adaptador no conoce esa política."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self._http = http

    async def obtener_factor(self, usuario_id: UUID, producto: str) -> Decimal:
        # ms-perfilamiento identifica al cliente con el mismo usuario_id que recibe
        # ms-cotizacion (bff-web le envía str(usuario_id) como cliente_id).
        respuesta = await self._http.get(f"/v1/ofertas-hipotecario/clientes/{usuario_id}/ultima")
        respuesta.raise_for_status()
        try:
            factor = Decimal(str(respuesta.json()["factor_ajuste"]))
        except (KeyError, InvalidOperation, ValueError) as exc:
            raise ValueError("ms-perfilamiento devolvió un factor_ajuste inválido") from exc
        if factor <= 0:
            raise ValueError("ms-perfilamiento devolvió un factor_ajuste no positivo")
        return factor


class AdaptadorPerfilRiesgoPorProducto:
    """Elige el proveedor de perfil según el producto: vida crediticia consulta a
    ms-perfilamiento; el resto sigue con su adaptador actual sin pagar esa llamada."""

    def __init__(self, por_producto: Mapping[str, AdaptadorPerfilRiesgo], por_defecto: AdaptadorPerfilRiesgo) -> None:
        self._por_producto = dict(por_producto)
        self._por_defecto = por_defecto

    async def obtener_factor(self, usuario_id: UUID, producto: str) -> Decimal:
        adaptador = self._por_producto.get(producto, self._por_defecto)
        return await adaptador.obtener_factor(usuario_id, producto)
