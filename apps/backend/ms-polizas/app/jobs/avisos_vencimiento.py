"""HU-67: orquestador de ciclo de vida -- genera los eventos "PolizaPorVencer"
que outbox-relay publica y notificaciones convierte en push, sin que nadie
llame GET /v1/polizas/por-vencer a mano.

Corre una vez y termina (no es un servidor): pensado para ser invocado por un
Kubernetes CronJob (manifiesto de Helm pendiente -- el chart genérico de
infra/k8s/charts/microservicio no tiene hoy un template de CronJob; agregarlo
es trabajo de infraestructura fuera del alcance de este cambio).

Uso: python -m app.jobs.avisos_vencimiento
"""

from __future__ import annotations

import asyncio
import logging

from app.application.casos_uso import generar_avisos_vencimiento
from app.config import Settings
from app.infrastructure.sql import crear_motor, fabrica_unidad_de_trabajo

logger = logging.getLogger(__name__)


async def main() -> None:
    config = Settings()
    logging.basicConfig(level=config.log_level)

    motor = crear_motor(config)
    try:
        uow = fabrica_unidad_de_trabajo(motor)
        generados = await generar_avisos_vencimiento(uow)
        logger.info("avisos_vencimiento_generados", extra={"cantidad": generados})
    finally:
        await motor.dispose()


if __name__ == "__main__":
    asyncio.run(main())
