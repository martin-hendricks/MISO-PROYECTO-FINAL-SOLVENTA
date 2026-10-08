import asyncio

import pytest

from app.aggregators.componer import componer
from app.clients.base import ServicioNoDisponible


async def _valor(v):
    return v


async def _falla():
    raise ServicioNoDisponible("ms-x")


async def _nunca_responde():
    await asyncio.Event().wait()


async def test_fuentes_en_paralelo_no_en_serie():
    a_arranco, b_arranco = asyncio.Event(), asyncio.Event()

    async def fuente_a():
        a_arranco.set()
        await b_arranco.wait()
        return "a"

    async def fuente_b():
        b_arranco.set()
        await a_arranco.wait()
        return "b"

    resultado = await asyncio.wait_for(componer(fuente_a(), {"b": fuente_b()}, timeout_opcional=5), timeout=2)

    assert (resultado.principal, resultado.opcionales) == ("a", {"b": "b"})
    assert resultado.degradado == []


async def test_opcional_que_no_responde_se_corta_y_se_marca_degradada():
    resultado = await componer(
        _valor("p"), {"lenta": _nunca_responde(), "falla": _falla()}, timeout_opcional=0.05
    )

    assert resultado.principal == "p"
    assert resultado.opcionales == {"lenta": None, "falla": None}
    assert resultado.degradado == ["lenta", "falla"]


async def test_si_falla_la_principal_falla_la_vista():
    with pytest.raises(ServicioNoDisponible):
        await componer(_falla(), {"a": _valor(1)}, timeout_opcional=1)
