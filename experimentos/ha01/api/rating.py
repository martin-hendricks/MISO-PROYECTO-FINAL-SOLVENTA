"""`:MotorRaiting` — motor de tarifa con costo de computo calibrado.

El costo es CONSTANTE entre brazos por construccion: es una variable
controlada, no una fuente de variacion. Se combina trabajo de CPU real
-para que compita por el event loop como lo haria un motor de reglas- con
una espera que ajusta el total al valor objetivo.

Advertencia honesta sobre la calibracion: con RATING_CPU_ITERS=1200 el
trabajo de CPU es del orden de decimas de milisegundo sobre un objetivo de
60 ms, asi que en la practica el costo es casi todo espera. Eso favorece a
todos los brazos por igual y no sesga la comparacion, pero SI hace que el
montaje no reproduzca la competencia por CPU de un motor de reglas real.
`scripts/calibrar_rating.py` mide el reparto y lo deja registrado para que
conste en el informe (amenaza a la validez del Anexo D).
"""
import asyncio
import hashlib

import asyncpg

from . import config

REGLAS_FALLBACK = {
    "VIAJE_BASICO": {"prima_base": 120000, "recargo_incertidumbre": 1.15},
}


class MotorTarifa:
    def __init__(self, reglas: dict) -> None:
        self.reglas = reglas or dict(REGLAS_FALLBACK)

    @classmethod
    async def desde_postgres(cls, url: str | None = None) -> "MotorTarifa":
        """Carga el conjunto de reglas AL ARRANQUE.

        PostgreSQL no participa del camino critico a proposito: la unica
        variable bajo estudio debe ser la resolucion del perfil.
        """
        url = url or config.DATABASE_URL
        conn = await asyncpg.connect(url)
        try:
            filas = await conn.fetch(
                "SELECT producto, prima_base, recargo_incertidumbre FROM reglas_tarifa"
            )
        finally:
            await conn.close()
        reglas = {
            f["producto"]: {
                "prima_base": float(f["prima_base"]),
                "recargo_incertidumbre": float(f["recargo_incertidumbre"]),
            }
            for f in filas
        }
        return cls(reglas)

    async def calcular(self, perfil: dict, producto: str, degradada: bool) -> int:
        loop = asyncio.get_running_loop()
        t0 = loop.time()

        h = hashlib.sha256()
        semilla = str(perfil.get("score_pago")).encode()
        for _ in range(config.RATING_CPU_ITERS):      # trabajo de CPU acotado
            h.update(semilla)

        regla = self.reglas.get(producto) or next(iter(self.reglas.values()))
        base = regla["prima_base"]
        factor = (2 - perfil["score_pago"]) * (1 + perfil["carga_financiera"])
        if degradada:
            # Una prima calculada sin senales frescas no puede costar lo
            # mismo que una calculada con ellas. El valor del recargo no lo
            # decide el experimento, pero su existencia hace visible que la
            # degradacion elegante tiene un precio de negocio.
            factor *= regla["recargo_incertidumbre"]

        restante = config.RATING_COST_S - (loop.time() - t0)
        if restante > 0:
            await asyncio.sleep(restante)
        return int(base * factor)
