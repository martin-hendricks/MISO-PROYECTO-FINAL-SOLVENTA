from datetime import datetime
from pydantic import BaseModel


class Poliza(BaseModel):
    numero: str
    producto: str
    suma_asegurada: float


class Hito(BaseModel):
    tipo: str
    descripcion: str
    actor: str
    ocurrido_en: datetime


class Documento(BaseModel):
    tipo: str
    estado: str
    cargado_en: datetime


class Peritaje(BaseModel):
    perito: str
    estado: str
    resultado: str | None = None
    agendado_para: datetime | None = None


class EstadoSiniestro(BaseModel):
    numero: str
    cliente_id: int
    estado: str
    causa: str
    monto_estimado: float | None = None
    monto_aprobado: float | None = None
    fecha_ocurrencia: datetime
    fecha_aviso: datetime
    poliza: Poliza
    hitos: list[Hito] = []
    documentos: list[Documento] = []
    peritaje: Peritaje | None = None
