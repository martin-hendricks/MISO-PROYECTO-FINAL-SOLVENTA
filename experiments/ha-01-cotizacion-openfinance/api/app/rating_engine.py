import asyncio

# Costo de cómputo fijo y calibrado (~60 ms), idéntico entre brazos, para
# que el motor de tarifa no sea una fuente de variación en la comparación
# (Anexo A: "Controlada — costo de cómputo del motor de tarifa").
_RATING_COST_SECONDS = 0.060


async def calcular_prima(cliente_id: int, perfil: dict | None) -> float:
    await asyncio.sleep(_RATING_COST_SECONDS)

    base = 150_000.0
    if perfil is None:
        # Perfil incompleto: el motor debe tolerarlo y reflejar la
        # incertidumbre con un recargo, no fallar.
        return base * 1.15

    endeudamiento = perfil.get("endeudamiento", 0.5)
    score = perfil.get("score_comportamiento_pago", 500)
    factor = 1.0 + endeudamiento * 0.4 - (score - 500) / 2000
    return round(base * max(factor, 0.5), 2)
