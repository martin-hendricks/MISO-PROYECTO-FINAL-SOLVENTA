from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.domain.evento import Cobertura, EventoInvalido


class CoberturaProveedor(BaseModel):
    """Bloque de cobertura que el proveedor (o el socio que vendió el seguro embebido)
    adjunta a la medición. Mismo formato para todos los proveedores simulados."""

    model_config = ConfigDict(extra="forbid")

    umbral: Decimal = Field(max_digits=18, decimal_places=4)
    monto: Decimal = Field(max_digits=14, decimal_places=2, gt=0)
    vigente: bool = True
    poliza_id: UUID | None = None
    poliza_numero: str | None = Field(default=None, max_length=60)
    usuario_id: UUID | None = None

    def a_dominio(self) -> Cobertura:
        return Cobertura(
            umbral=self.umbral,
            monto=self.monto,
            vigente=self.vigente,
            poliza_id=self.poliza_id,
            poliza_numero=self.poliza_numero,
            usuario_id=self.usuario_id,
        )


def validar[M: BaseModel](modelo: type[M], carga: dict, proveedor: str) -> M:
    try:
        return modelo.model_validate(carga)
    except ValidationError as exc:
        campos = sorted({".".join(str(p) for p in e["loc"]) for e in exc.errors()})
        raise EventoInvalido(
            "esquema_proveedor_invalido", f"Carga de '{proveedor}' inválida en: {', '.join(campos)}"
        ) from exc
