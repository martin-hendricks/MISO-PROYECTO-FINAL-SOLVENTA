from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from dataclasses import dataclass, field
from typing import Any

from app.clients.base import RecursoNoEncontrado, ServicioNoDisponible


@dataclass
class Composicion:
    principal: Any
    opcionales: dict[str, Any] = field(default_factory=dict)
    degradado: list[str] = field(default_factory=list)


async def _opcional(tarea: Awaitable[Any], timeout: float) -> Any:
    try:
        return await asyncio.wait_for(tarea, timeout)
    except (TimeoutError, ServicioNoDisponible, RecursoNoEncontrado):
        return _FALLO


_FALLO = object()


async def componer(
    principal: Awaitable[Any],
    opcionales: dict[str, Awaitable[Any]],
    timeout_opcional: float,
) -> Composicion:
    nombres = list(opcionales)
    resultado_principal, *resultados = await asyncio.gather(
        principal, *(_opcional(opcionales[n], timeout_opcional) for n in nombres)
    )
    composicion = Composicion(principal=resultado_principal)
    for nombre, valor in zip(nombres, resultados, strict=True):
        if valor is _FALLO:
            composicion.opcionales[nombre] = None
            composicion.degradado.append(nombre)
        else:
            composicion.opcionales[nombre] = valor
    return composicion
