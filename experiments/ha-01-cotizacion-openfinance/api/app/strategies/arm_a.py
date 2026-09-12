"""Brazo A — línea base: invocación bloqueante al proveedor en cada
cotización, sin caché y sin presupuesto de abandono. El camino crítico
espera lo que el proveedor tarde, hasta el timeout duro del adaptador."""

from .. import adaptador_of
from ..rating_engine import calcular_prima


async def resolver_oferta(cliente_id: int) -> tuple[float, str]:
    perfil = await adaptador_of.consultar_perfil(cliente_id)
    prima = await calcular_prima(cliente_id, perfil)
    origen = "fresco" if perfil is not None else "respaldo_default"
    return prima, origen
