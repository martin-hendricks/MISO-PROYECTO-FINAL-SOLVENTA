from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.modelos import Consentimiento


class OtorgarConsentimientoEntrada(BaseModel):
    cliente_id: str = Field(min_length=1, max_length=120)


class ConsentimientoSalida(BaseModel):
    id: UUID
    cliente_id: str
    otorgado_en: datetime
    revocado_en: datetime | None
    vigente: bool

    @classmethod
    def desde(cls, consentimiento: Consentimiento) -> "ConsentimientoSalida":
        return cls(
            id=consentimiento.id,
            cliente_id=consentimiento.cliente_id,
            otorgado_en=consentimiento.otorgado_en,
            revocado_en=consentimiento.revocado_en,
            vigente=consentimiento.vigente,
        )


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
