import asyncio
from datetime import UTC, datetime

import pytest

from app.application.relay import (
    ESQUEMAS_PERMITIDOS,
    FuenteOutbox,
    bucle_relay,
    ejecutar_ciclo,
    validar_esquema,
)

from .dobles import PublicadorDoble, RepositorioOutboxDoble, evento_outbox


class TestValidarEsquema:
    def test_esquema_permitido_se_devuelve_tal_cual(self):
        assert validar_esquema("ms_cotizacion") == "ms_cotizacion"

    @pytest.mark.parametrize("esquema", sorted(ESQUEMAS_PERMITIDOS))
    def test_todos_los_esquemas_permitidos_pasan(self, esquema):
        assert validar_esquema(esquema) == esquema

    def test_esquema_no_permitido_lanza(self):
        with pytest.raises(ValueError, match="no permitido"):
            validar_esquema("ms_desconocido")

    @pytest.mark.parametrize(
        "esquema",
        ["", "123_invalido", "ms-cotizacion", "ms_cotizacion; drop table x", None, 42],
    )
    def test_esquema_con_formato_invalido_lanza(self, esquema):
        with pytest.raises(ValueError, match="inválido"):
            validar_esquema(esquema)


class TestEjecutarCiclo:
    async def test_publica_pendientes_de_una_fuente(self, publicador):
        evento = evento_outbox()
        repositorio = RepositorioOutboxDoble("ms_cotizacion", [evento])

        total = await ejecutar_ciclo([repositorio], publicador, lote=10, ahora=datetime.now(UTC))

        assert total == 1
        assert publicador.publicados == [evento]
        assert repositorio.pendientes == []

    async def test_sin_pendientes_devuelve_cero(self, publicador, repositorio):
        total = await ejecutar_ciclo([repositorio], publicador, lote=10, ahora=datetime.now(UTC))
        assert total == 0

    async def test_respeta_el_tamano_de_lote(self, publicador):
        eventos = [evento_outbox() for _ in range(5)]
        repositorio = RepositorioOutboxDoble("ms_cotizacion", eventos)

        total = await ejecutar_ciclo([repositorio], publicador, lote=2, ahora=datetime.now(UTC))

        assert total == 2
        assert len(repositorio.pendientes) == 3

    async def test_suma_el_total_de_varias_fuentes(self, publicador):
        repo_a = RepositorioOutboxDoble("ms_cotizacion", [evento_outbox()])
        repo_b = RepositorioOutboxDoble("ms_pagos", [evento_outbox(), evento_outbox()])

        total = await ejecutar_ciclo(
            [repo_a, repo_b], publicador, lote=10, ahora=datetime.now(UTC)
        )

        assert total == 3

    async def test_una_fuente_caida_no_frena_las_demas(self, publicador):
        repo_caido = RepositorioOutboxDoble("ms_cotizacion")
        repo_caido.fallar = RuntimeError("base caída")
        repo_sano = RepositorioOutboxDoble("ms_pagos", [evento_outbox()])

        total = await ejecutar_ciclo(
            [repo_caido, repo_sano], publicador, lote=10, ahora=datetime.now(UTC)
        )

        assert total == 1
        assert len(publicador.publicados) == 1


class TestBucleRelay:
    async def test_se_detiene_cuando_el_event_se_activa(self, publicador, repositorio):
        parar = asyncio.Event()
        parar.set()  # ya activado: el bucle no debe ejecutar ningún ciclo

        await asyncio.wait_for(
            bucle_relay([repositorio], publicador, lote=10, intervalo_segundos=5, parar=parar),
            timeout=1,
        )

        assert publicador.publicados == []

    async def test_ejecuta_al_menos_un_ciclo_antes_de_esperar(self, publicador):
        evento = evento_outbox()
        repositorio = RepositorioOutboxDoble("ms_cotizacion", [evento])
        parar = asyncio.Event()

        tarea = asyncio.create_task(
            bucle_relay([repositorio], publicador, lote=10, intervalo_segundos=5, parar=parar)
        )
        await asyncio.wait_for(repositorio.llamado.wait(), timeout=1)
        parar.set()
        await asyncio.wait_for(tarea, timeout=1)

        assert evento in publicador.publicados

    async def test_un_ciclo_que_lanza_no_mata_el_bucle(self, publicador):
        repositorio = RepositorioOutboxDoble("ms_cotizacion")
        repositorio.fallar = RuntimeError("fallo inesperado del ciclo")
        parar = asyncio.Event()

        tarea = asyncio.create_task(
            bucle_relay([repositorio], publicador, lote=10, intervalo_segundos=5, parar=parar)
        )
        await asyncio.wait_for(repositorio.llamado.wait(), timeout=1)
        parar.set()
        # No debe lanzar ni colgarse: el bucle captura el fallo y sigue
        # reintentando hasta que `parar` lo detiene.
        await asyncio.wait_for(tarea, timeout=1)


def test_fuente_outbox_guarda_esquema_y_url():
    fuente = FuenteOutbox("ms_cotizacion", "postgresql+asyncpg://localhost/solventa")
    assert fuente.esquema == "ms_cotizacion"
    assert fuente.database_url == "postgresql+asyncpg://localhost/solventa"
