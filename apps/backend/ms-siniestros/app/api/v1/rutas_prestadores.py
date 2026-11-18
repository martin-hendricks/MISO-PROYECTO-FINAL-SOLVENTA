from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.application import prestadores as casos
from app.dependencies import obtener_uow
from app.ports.persistencia import FabricaUnidadDeTrabajo
from app.seguridad import LlamanteDep

from .schemas_prestadores import (
    BusquedaSalida,
    EstadoEntrada,
    PrestadorEdicion,
    PrestadorEntrada,
    PrestadorSalida,
    SiniestroPrestadoresSalida,
    consulta_desde,
)

router = APIRouter(prefix="/v1", tags=["prestadores"])
Uow = Annotated[FabricaUnidadDeTrabajo, Depends(obtener_uow)]


@router.get("/prestadores", response_model=BusquedaSalida)
async def listar_prestadores(
    uow: Uow,
    llamante: LlamanteDep,
    lat: Annotated[Decimal | None, Query()] = None,
    lng: Annotated[Decimal | None, Query()] = None,
    ciudad: Annotated[str | None, Query()] = None,
    ramo: Annotated[str | None, Query()] = None,
    radio_km: Annotated[Decimal | None, Query(gt=0, le=50)] = None,
    estado: Annotated[str | None, Query(pattern="^(activo|inactivo)$")] = None,
    limite: Annotated[int, Query(ge=1, le=100)] = 50,
):
    consulta = consulta_desde(lat, lng, ciudad, ramo, radio_km or Decimal("10"), estado, limite)
    return BusquedaSalida.desde(await casos.buscar(uow, llamante, consulta))


@router.get("/prestadores/{prestador_id}", response_model=PrestadorSalida)
async def obtener_prestador(prestador_id: str, uow: Uow, llamante: LlamanteDep):
    return PrestadorSalida.desde(await casos.obtener(uow, llamante, prestador_id))


@router.get("/siniestros/{siniestro_id}/prestadores", response_model=SiniestroPrestadoresSalida)
async def prestadores_del_siniestro(
    siniestro_id: UUID,
    uow: Uow,
    llamante: LlamanteDep,
    radio_km: Annotated[Decimal, Query(gt=0, le=50)] = Decimal("10"),
    limite: Annotated[int, Query(ge=1, le=100)] = 50,
):
    resultado = await casos.buscar_por_siniestro(uow, llamante, siniestro_id, radio_km, limite)
    siniestro = resultado["siniestro"]
    centro = resultado["centro"]
    return SiniestroPrestadoresSalida(
        siniestro={
            "id": str(siniestro.id),
            "numero": siniestro.numero,
            "ramo": resultado["ramo_fijo"],
            "geo": None
            if siniestro.geo is None
            else {"lat": siniestro.geo.lat, "lng": siniestro.geo.lng},
        },
        ramo_fijo=resultado["ramo_fijo"],
        sin_geoetiqueta=resultado["sin_geoetiqueta"],
        centro=None if centro is None else {"lat": centro.lat, "lng": centro.lng, "origen": centro.origen},
        radio_km=resultado["radio_km"],
        prestadores=[PrestadorSalida.desde_cercano(fila) for fila in resultado["prestadores"]],
    )


@router.post("/prestadores", response_model=PrestadorSalida, status_code=201)
async def crear_prestador(cuerpo: PrestadorEntrada, uow: Uow, llamante: LlamanteDep):
    return PrestadorSalida.desde(await casos.crear(uow, llamante, cuerpo.a_dominio()))


@router.patch("/prestadores/{prestador_id}", response_model=PrestadorSalida)
async def editar_prestador(prestador_id: str, cuerpo: PrestadorEdicion, uow: Uow, llamante: LlamanteDep):
    return PrestadorSalida.desde(await casos.editar(uow, llamante, prestador_id, cuerpo.a_dominio()))


@router.post("/prestadores/{prestador_id}/estado", response_model=PrestadorSalida)
async def cambiar_estado(prestador_id: str, cuerpo: EstadoEntrada, uow: Uow, llamante: LlamanteDep):
    return PrestadorSalida.desde(await casos.cambiar_estado(uow, llamante, prestador_id, cuerpo.estado))
