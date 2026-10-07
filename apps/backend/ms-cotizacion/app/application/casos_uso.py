from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from uuid import UUID

from app.config import Settings
from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import SolicitudCotizacion, solicitud_recibida
from app.domain.oferta import ConsultaOferta, Oferta, oferta_emitida
from app.domain.rating import ReglaRating, ResultadoPrima, calcular_prima
from app.domain.riesgo import FactorRiesgo, OrigenFactorRiesgo, aplicar_factor_riesgo
from app.ports.catalogo import CatalogoProductos
from app.ports.persistencia import ClaveIdempotenciaDuplicada, FabricaUnidadDeTrabajo
from app.ports.riesgo import AdaptadorPerfilRiesgo


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


async def _obtener_factor_con_respaldo(
    config: Settings, adaptador: AdaptadorPerfilRiesgo, usuario_id: UUID, producto: str
) -> FactorRiesgo:
    try:
        valor = await asyncio.wait_for(
            adaptador.obtener_factor(usuario_id, producto),
            timeout=config.factor_riesgo_timeout_maximo_ms / 1000,
        )
        return FactorRiesgo(valor=valor, origen=OrigenFactorRiesgo.REAL)
    except Exception:
        # Ancho deliberado: el Gherkin exige degradar igual si el adaptador "falla o
        # llega tarde", sin distinguir el tipo de fallo. El core no debe acoplarse a
        # qué excepciones lanza un proveedor real de Open Finance — ver ports/riesgo.py.
        return FactorRiesgo(valor=config.factor_riesgo_valor_respaldo, origen=OrigenFactorRiesgo.RESPALDO)


async def combinar_factor_riesgo(
    config: Settings,
    adaptador: AdaptadorPerfilRiesgo,
    usuario_id: UUID,
    producto: str,
    resultado: ResultadoPrima,
) -> tuple[ResultadoPrima, FactorRiesgo]:
    """Cálculo + resiliencia pura: no escribe outbox ni persiste nada. HU-99/SOLV-99 la
    orquesta junto con calcular_prima_solicitud."""
    factor = await _obtener_factor_con_respaldo(config, adaptador, usuario_id, producto)
    return aplicar_factor_riesgo(resultado, factor), factor


@dataclass(frozen=True)
class RegistroOferta:
    solicitud: SolicitudCotizacion
    oferta: Oferta
    creada: bool


async def cotizar(
    uow: FabricaUnidadDeTrabajo,
    catalogo: CatalogoProductos,
    adaptador_riesgo: AdaptadorPerfilRiesgo,
    config: Settings,
    idempotency_key: str,
    usuario_id: UUID,
    socio_id: UUID,
    consentimiento_id: UUID,
    producto: str,
    canal: str,
    datos_riesgo: dict[str, Any],
) -> RegistroOferta:
    """Orquesta HU-96+HU-97+HU-98 en un único flujo: la oferta es la respuesta del mismo
    flujo de recibir_solicitud, sin exigir una segunda llamada."""
    async with uow() as tx:
        existente = await tx.solicitudes.obtener_por_clave(idempotency_key)
        if existente is not None:
            oferta_existente = await tx.ofertas.obtener_por_solicitud(existente.id)
            return RegistroOferta(existente, oferta_existente, creada=False)

    solicitud = SolicitudCotizacion.crear(
        idempotency_key, usuario_id, socio_id, consentimiento_id, producto, canal, datos_riesgo, catalogo
    )
    # calcular_prima_solicitud y combinar_factor_riesgo abren su propia transacción de
    # lectura (HU-97/HU-98, sin cambios); son lecturas y no participan del commit final.
    regla, resultado = await calcular_prima_solicitud(uow, producto, datos_riesgo)
    resultado, factor = await combinar_factor_riesgo(config, adaptador_riesgo, usuario_id, producto, resultado)
    definicion = catalogo.obtener(producto)
    oferta = Oferta.emitir(
        solicitud, regla, resultado, factor, definicion.coberturas, timedelta(minutes=config.oferta_vigencia_minutos)
    )
    solicitud.marcar_cotizada()

    async with uow() as tx:
        await tx.solicitudes.agregar(solicitud)
        await tx.ofertas.agregar(oferta)
        await tx.outbox.agregar(solicitud_recibida(solicitud))
        await tx.outbox.agregar(oferta_emitida(oferta))
        try:
            await tx.confirmar()
            return RegistroOferta(solicitud, oferta, creada=True)
        except ClaveIdempotenciaDuplicada:
            pass

    async with uow() as tx:
        ganador_solicitud = await tx.solicitudes.obtener_por_clave(idempotency_key)
        ganador_oferta = await tx.ofertas.obtener_por_solicitud(ganador_solicitud.id)
    return RegistroOferta(ganador_solicitud, ganador_oferta, creada=False)


@dataclass(frozen=True)
class ReconsultaOferta:
    solicitud: SolicitudCotizacion
    consulta: ConsultaOferta


async def reconsultar_oferta(uow: FabricaUnidadDeTrabajo, cotizacion_id: UUID) -> ReconsultaOferta:
    """Lectura pura: no invoca calcular_prima_solicitud ni combinar_factor_riesgo ni el
    adaptador de perfil. 404 genérico sin distinguir el motivo (solicitud inexistente vs.
    sin oferta), para no filtrar si la cotización perteneció a otro cliente/socio."""
    async with uow() as tx:
        solicitud = await tx.solicitudes.obtener(cotizacion_id)
        oferta = await tx.ofertas.obtener_por_solicitud(cotizacion_id) if solicitud is not None else None
    if solicitud is None or oferta is None:
        raise NoEncontrado(f"Cotización {cotizacion_id} no existe")
    return ReconsultaOferta(solicitud, ConsultaOferta.desde(oferta))
