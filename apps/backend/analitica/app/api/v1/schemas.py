from datetime import date

from pydantic import BaseModel

from app.domain.modelos import ConteoEventos


class ConteoSalida(BaseModel):
    tipo: str
    fecha: date
    cantidad: int

    @classmethod
    def desde(cls, conteo: ConteoEventos) -> "ConteoSalida":
        return cls(tipo=conteo.tipo, fecha=conteo.fecha, cantidad=conteo.cantidad)


class MetricasSalida(BaseModel):
    conteos: list[ConteoSalida]


class ErrorSalida(BaseModel):
    codigo: str
    mensaje: str
