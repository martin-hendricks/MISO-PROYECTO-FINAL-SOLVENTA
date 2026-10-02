from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..dependencies import require_roles
from .cliente import OFFER, _offer

router = APIRouter(
    prefix="/asesor",
    tags=["asesor"],
    dependencies=[Depends(require_roles("asesor"))],
)


class VentaAsistida(BaseModel):
    clienteId: str = Field(min_length=1)
    ramo: str
    datosRiesgo: dict


class ClienteNuevo(BaseModel):
    nombre: str
    documento: str
    correo: str
    habeasData: bool
    estado: str = "activo"


class Desactivar(BaseModel):
    clienteId: str
    estado: str


@router.post("/cotizaciones")
def venta(body: VentaAsistida) -> dict:
    offer = _offer(OFFER["cotizacionId"])
    offer["ramo"] = body.ramo
    return offer


@router.get("/cartera")
def cartera() -> dict:
    return {
        "kpis": {"cotizaciones": 12, "polizas": 40},
        "cola": [
            {
                "id": "COT-1042",
                "tipo": "cotizacion",
                "ramo": "Protección de dispositivo",
                "estado": "en_revision",
            },
            {
                "id": "POL-88219-CO",
                "tipo": "poliza",
                "ramo": "Protección de dispositivo",
                "estado": "vigente",
            },
        ],
    }


@router.get("/clientes")
def listar() -> dict:
    return {
        "clientes": [
            {
                "clienteId": "CLI-18",
                "nombre": "Camila Restrepo",
                "documento": "1012345678",
                "correo": "camila@correo.com",
                "habeasData": True,
                "estado": "activo",
            }
        ]
    }


@router.post("/clientes")
def crear(body: ClienteNuevo) -> dict:
    created = body.model_dump()
    created["clienteId"] = "CLI-19"
    return created


@router.post("/clientes/estado")
def desactivar(body: Desactivar) -> dict:
    return {"clienteId": body.clienteId, "estado": "inactivo"}
