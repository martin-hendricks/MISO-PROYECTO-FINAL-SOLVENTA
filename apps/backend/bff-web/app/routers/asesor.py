from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..dependencies import require_roles
from .cliente import OFFER, _offer

router = APIRouter(
    prefix="/asesor",
    tags=["asesor"],
    dependencies=[Depends(require_roles("asesor"))],
)


def _cliente(
    cliente_id: str,
    nombre: str,
    documento: str,
    canal: str,
    estado: str,
    consentimiento: str,
) -> dict:
    return {
        "clienteId": cliente_id,
        "nombre": nombre,
        "documento": documento,
        "correo": f"{nombre.split()[0].lower()}@correo.com",
        "habeasData": consentimiento != "revocado",
        "estado": estado,
        "canal": canal,
        "consentimiento": consentimiento,
    }


CLIENTES = [
    _cliente("CLI-18", "Andrés Gómez", "1020334556", "web", "activo", "habeas_data"),
    _cliente("CLI-19", "Laura Peña", "52448901", "android", "activo", "habeas_data"),
    _cliente("CLI-20", "Ricardo Salas", "80112334", "web", "activo", "hipotecario_pendiente"),
    _cliente("CLI-21", "Marcela Ruiz", "41778220", "android", "activo", "habeas_data"),
    _cliente("CLI-22", "Julián Torres", "79330114", "web", "inactivo", "revocado"),
]


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
    return {"clientes": [dict(cliente) for cliente in CLIENTES]}


@router.post("/clientes")
def crear(body: ClienteNuevo) -> dict:
    created = body.model_dump()
    created["clienteId"] = "CLI-23"
    return created


@router.post("/clientes/estado")
def desactivar(body: Desactivar) -> dict:
    return {"clienteId": body.clienteId, "estado": "inactivo"}
