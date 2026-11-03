from fastapi import Request

from app.ports.kyc import VerificadorKYC
from app.ports.persistencia import FabricaUnidadDeTrabajo


def obtener_uow(request: Request) -> FabricaUnidadDeTrabajo:
    return request.app.state.fabrica_uow


def obtener_verificador_kyc(request: Request) -> VerificadorKYC:
    return request.app.state.verificador_kyc
