"""Cubre app/jobs/avisos_vencimiento.py (entrypoint del job de HU-67) con
los constructores de infraestructura real mockeados -- sin Postgres real.
generar_avisos_vencimiento() ya está testeado contra un UoW en memoria en
tests/test_casos_uso.py; aquí solo se cubre el cableado del script."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from app.jobs.avisos_vencimiento import main


async def test_main_construye_motor_corre_el_caso_de_uso_y_libera_el_motor():
    motor_falso = MagicMock()
    motor_falso.dispose = AsyncMock()

    with (
        patch("app.jobs.avisos_vencimiento.crear_motor", return_value=motor_falso) as crear_motor_mock,
        patch("app.jobs.avisos_vencimiento.fabrica_unidad_de_trabajo", return_value="uow-falso") as fabrica_mock,
        patch("app.jobs.avisos_vencimiento.generar_avisos_vencimiento", AsyncMock(return_value=3)) as generar_mock,
    ):
        await main()

    crear_motor_mock.assert_called_once()
    fabrica_mock.assert_called_once_with(motor_falso)
    generar_mock.assert_awaited_once_with("uow-falso")
    motor_falso.dispose.assert_awaited_once()


async def test_main_libera_el_motor_aunque_el_caso_de_uso_falle():
    motor_falso = MagicMock()
    motor_falso.dispose = AsyncMock()

    with (
        patch("app.jobs.avisos_vencimiento.crear_motor", return_value=motor_falso),
        patch("app.jobs.avisos_vencimiento.fabrica_unidad_de_trabajo", return_value="uow-falso"),
        patch(
            "app.jobs.avisos_vencimiento.generar_avisos_vencimiento",
            AsyncMock(side_effect=RuntimeError("fallo simulado del caso de uso")),
        ),
    ):
        try:
            await main()
            assert False, "main() debería propagar el fallo del caso de uso"
        except RuntimeError:
            pass

    motor_falso.dispose.assert_awaited_once()
