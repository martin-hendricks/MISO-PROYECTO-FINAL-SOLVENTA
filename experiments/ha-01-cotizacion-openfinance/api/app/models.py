from pydantic import BaseModel


class OfertaSeguro(BaseModel):
    cliente_id: int
    prima: float
    moneda: str = "COP"
    origen_perfil: str  # "fresco" | "cache" | "respaldo_default"
    edad_dato_ms: float | None = None
    brazo: str
