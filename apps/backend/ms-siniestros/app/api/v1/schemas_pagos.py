from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel

from app.application.casos_uso import PagosRecibidos
from app.domain.modelos import PagoRecibido


class PagoRecibidoSalida(BaseModel):
    siniestro_id: UUID
    numero: str | None
    tipo: str
    ramo: str | None
    poliza_numero: str | None
    descripcion: str | None
    monto: Decimal
    comprobante: str
    clave: str
    pagado_en: datetime

    @classmethod
    def desde(cls, pago: PagoRecibido) -> "PagoRecibidoSalida":
        return cls(
            siniestro_id=pago.siniestro_id,
            numero=pago.numero,
            tipo=pago.tipo.value,
            ramo=pago.ramo,
            poliza_numero=pago.poliza_numero,
            descripcion=pago.descripcion,
            monto=pago.monto,
            comprobante=pago.comprobante,
            clave=pago.clave,
            pagado_en=pago.pagado_en,
        )


class PagosRecibidosSalida(BaseModel):
    moneda: str
    total: Decimal
    pagos: list[PagoRecibidoSalida]

    @classmethod
    def desde(cls, resultado: PagosRecibidos) -> "PagosRecibidosSalida":
        return cls(
            moneda=resultado.moneda,
            total=resultado.total,
            pagos=[PagoRecibidoSalida.desde(p) for p in resultado.pagos],
        )
