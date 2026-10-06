from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies import require_roles

router = APIRouter(
    prefix="/cliente",
    tags=["cliente"],
    dependencies=[Depends(require_roles("cliente"))],
)

OFFER = {
    "cotizacionId": "COT-1042",
    "ramo": "Protección de dispositivo",
    "estado": "oferta_vigente",
    "prima": 89000,
    "moneda": "COP",
    "venceEn": "2026-10-01",
}
POLICY = {
    "numero": "POL-88219-CO",
    "ramo": "Protección de dispositivo",
    "estado": "vigente",
    "venceEn": "2027-03-12",
}
REFUSAL = {"estado": "rechazada", "motivo": "Valor del equipo fuera de rango"}
PAYMENT = {
    "siniestroId": "SIN-220",
    "poliza": "POL-11002-CO",
    "umbral": "retraso mayor a 120 min",
    "monto": 250000,
    "moneda": "COP",
    "estado": "pagado",
}


class Cotizacion(BaseModel):
    ramo: str
    datosRiesgo: dict
    clienteId: str | None = None


class Aceptar(BaseModel):
    cotizacionId: str


class Credito(BaseModel):
    valor: int
    plazoMeses: int


class Hipoteca(BaseModel):
    credito: Credito
    consentimientoPerfil: bool


def _offer(cotizacion_id: str) -> dict:
    body = dict(OFFER)
    body["cotizacionId"] = cotizacion_id
    return body


@router.post("/cotizaciones")
def cotizar(body: Cotizacion) -> dict:
    if body.clienteId:
        raise HTTPException(status_code=400, detail="La venta asistida no es de este canal")
    return _offer(OFFER["cotizacionId"])


@router.get("/cotizaciones/{cotizacion_id}")
def reconsultar(cotizacion_id: str) -> dict:
    return _offer(cotizacion_id)


@router.post("/polizas")
def emitir(body: Aceptar) -> dict:
    if body.cotizacionId == "COT-RECHAZADA":
        return REFUSAL
    return dict(POLICY)


@router.get("/polizas")
def billetera() -> dict:
    return {
        "polizas": [
            {
                "numero": "POL-88219-CO",
                "ramo": "Protección de dispositivo",
                "resumen": "Robo, Pantalla, Hurto",
                "estado": "vigente",
                "venceEn": "2027-03-12",
            }
        ]
    }


@router.get("/polizas/{numero}")
def detalle(numero: str) -> dict:
    return {
        "numero": numero,
        "ramo": "Protección de dispositivo",
        "resumen": "Robo y Pantalla",
        "estado": "vigente",
        "venceEn": "2027-03-12",
        "queHacer": "Toma la foto del daño y anota fecha y lugar.",
    }


@router.get("/pagos-automaticos")
def pagos() -> dict:
    return dict(PAYMENT)


@router.post("/oferta-hipotecaria")
def hipoteca(body: Hipoteca) -> dict:
    if body.consentimientoPerfil:
        return {
            "ramo": "Vida crediticia",
            "estado": "oferta_vigente",
            "prima": 64000,
            "moneda": "COP",
            "factores": ["plazo", "valor del crédito"],
            "degradada": False,
        }
    return {
        "ramo": "Vida crediticia",
        "estado": "oferta_vigente",
        "prima": 50000,
        "moneda": "COP",
        "factores": ["plazo", "valor del crédito"],
        "degradada": True,
    }


@router.get("/inicio")
def inicio() -> dict:
    return {
        "ofertaVigente": {
            "cotizacionId": "COT-1042",
            "ramo": "Protección de dispositivo",
            "estado": "oferta_vigente",
        },
        "poliza": {
            "numero": "POL-88219-CO",
            "ramo": "Protección de dispositivo",
            "estado": "vigente",
        },
        "siniestroEnCurso": {"siniestroId": "SIN-441", "estado": "en_evaluacion"},
        "hipotecario": None,
    }
