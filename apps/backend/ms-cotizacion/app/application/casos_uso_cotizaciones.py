from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.domain.errores import ReglaDeNegocioViolada
from app.domain.modelos import SolicitudCotizacion, solicitud_recibida
from app.domain.rating import ReglaRating, ResultadoPrima, calcular_prima
from app.ports.catalogo import CatalogoProductos
from app.ports.persistencia import ClaveIdempotenciaDuplicada, FabricaUnidadDeTrabajo


@dataclass(frozen=True)
class RegistroSolicitud:
    solicitud: SolicitudCotizacion
    creada: bool


async def recibir_solicitud(
    uow: FabricaUnidadDeTrabajo,
    catalogo: CatalogoProductos,
    idempotency_key: str,
    usuario_id: UUID,
    socio_id: UUID,
    consentimiento_id: UUID,
    producto: str,
    canal: str,
    datos_riesgo: dict[str, Any],
) -> RegistroSolicitud:
    async with uow() as tx:
        existente = await tx.solicitudes.obtener_por_clave(idempotency_key)
        if existente is not None:
            return RegistroSolicitud(existente, creada=False)

        solicitud = SolicitudCotizacion.crear(
            idempotency_key, usuario_id, socio_id, consentimiento_id, producto, canal, datos_riesgo, catalogo
        )
        await tx.solicitudes.agregar(solicitud)
        await tx.outbox.agregar(solicitud_recibida(solicitud))
        try:
            await tx.confirmar()
            return RegistroSolicitud(solicitud, creada=True)
        except ClaveIdempotenciaDuplicada:
            pass

    async with uow() as tx:
        ganador = await tx.solicitudes.obtener_por_clave(idempotency_key)
    if ganador is None:
        raise RuntimeError("Clave duplicada sin registro visible")
    return RegistroSolicitud(ganador, creada=False)


async def calcular_prima_solicitud(
    uow: FabricaUnidadDeTrabajo, producto: str, datos_riesgo: dict[str, Any]
) -> tuple[ReglaRating, ResultadoPrima]:
    """Solo lectura + cálculo puro: no escribe outbox ni cambia estado. El evento de
    oferta se publica en HU-99/SOLV-99 cuando se persiste la Oferta completa."""
    async with uow() as tx:
        regla = await tx.reglas_rating.obtener_vigente(producto)
    if regla is None:
        raise ReglaDeNegocioViolada("regla_rating_no_configurada", f"No hay regla de rating vigente para '{producto}'")
    resultado = calcular_prima(regla, datos_riesgo)
    return regla, resultado
