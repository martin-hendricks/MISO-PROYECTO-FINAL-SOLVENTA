from __future__ import annotations

import asyncio
from dataclasses import dataclass

from app.config import Settings
from app.domain.errores import ConsentimientoNoOtorgado, NoEncontrado
from app.domain.modelos import (
    AtributoPerfil,
    Consentimiento,
    EstadoAdaptador,
    OrigenAdaptador,
    Oferta,
    Perfil,
    consentimiento_otorgado,
    consentimiento_revocado,
    oferta_emitida,
)
from app.domain.precio import ANTIGUEDAD_DOCUMENTO, NIVEL_INGRESOS_ESTIMADO, SCORE_COMPORTAMIENTO, ZONA_RIESGO, calcular_oferta
from app.ports.adaptadores import AdaptadorOpenData, AdaptadorOpenFinance
from app.ports.persistencia import ClaveIdempotenciaDuplicada, FabricaUnidadDeTrabajo


@dataclass(frozen=True)
class RegistroConsentimiento:
    consentimiento: Consentimiento
    creado: bool


async def otorgar_consentimiento(uow: FabricaUnidadDeTrabajo, cliente_id: str) -> RegistroConsentimiento:
    """HU-53: acción explícita del cliente, nunca implícita. Queda con marca de tiempo
    y es auditable vía outbox. Si ya existe un consentimiento vigente, es idempotente:
    no crea uno nuevo (`creado=False`)."""
    async with uow() as tx:
        vigente = await tx.consentimientos.obtener_vigente(cliente_id)
        if vigente is not None:
            return RegistroConsentimiento(vigente, creado=False)

        consentimiento = Consentimiento.otorgar(cliente_id)
        await tx.consentimientos.agregar(consentimiento)
        await tx.outbox.agregar(consentimiento_otorgado(consentimiento))
        await tx.confirmar()
    return RegistroConsentimiento(consentimiento, creado=True)


async def revocar_consentimiento(uow: FabricaUnidadDeTrabajo, cliente_id: str) -> Consentimiento:
    """HU-53: revocar impide futuras consultas de perfil. Efectivo de inmediato: la
    siguiente llamada a consultar_consentimiento_vigente/perfilar_y_ofertar ya no
    encuentra consentimiento vigente, porque no hay caché intermedia — se lee siempre
    el último estado persistido."""
    async with uow() as tx:
        vigente = await tx.consentimientos.obtener_vigente(cliente_id)
        if vigente is None:
            raise NoEncontrado(f"El cliente {cliente_id} no tiene consentimiento de perfilamiento vigente")
        vigente.revocar()
        await tx.consentimientos.actualizar(vigente)
        await tx.outbox.agregar(consentimiento_revocado(vigente))
        await tx.confirmar()
    return vigente


async def consultar_consentimiento_vigente(uow: FabricaUnidadDeTrabajo, cliente_id: str) -> Consentimiento | None:
    async with uow() as tx:
        return await tx.consentimientos.obtener_vigente(cliente_id)


async def _atributos_con_respaldo(
    adaptador_open_finance: AdaptadorOpenFinance,
    adaptador_open_data: AdaptadorOpenData,
    cliente_id: str,
    config: Settings,
) -> list[AtributoPerfil]:
    """HU-54 + HU-56: invoca cada adaptador con su propio timeout (asyncio.wait_for).
    Si expira o el adaptador lanza cualquier excepción, sustituye por el valor de
    respaldo marcando degradado=True para ESE atributo. Nunca silencioso: el estado
    (éxito/degradado) queda explícito en cada AtributoPerfil, que luego se persiste
    como parte del resultado del perfilamiento."""

    async def _invocar_open_finance() -> list[AtributoPerfil]:
        try:
            datos = await asyncio.wait_for(
                adaptador_open_finance.obtener_atributos(cliente_id),
                timeout=config.timeout_open_finance_ms / 1000,
            )
            return [
                AtributoPerfil(
                    nombre=NIVEL_INGRESOS_ESTIMADO,
                    valor=datos[NIVEL_INGRESOS_ESTIMADO],
                    origen=OrigenAdaptador.OPEN_FINANCE,
                    estado=EstadoAdaptador.EXITO,
                    degradado=False,
                ),
                AtributoPerfil(
                    nombre=SCORE_COMPORTAMIENTO,
                    valor=datos[SCORE_COMPORTAMIENTO],
                    origen=OrigenAdaptador.OPEN_FINANCE,
                    estado=EstadoAdaptador.EXITO,
                    degradado=False,
                ),
            ]
        except Exception:
            # Ancho deliberado (igual que ms-cotizacion/app/application/casos_uso_cotizaciones.py):
            # el Gherkin de HU-56 exige degradar igual si el adaptador "excede su tiempo
            # límite o falla", sin distinguir TimeoutError de cualquier otra excepción.
            # El núcleo no debe acoplarse a qué excepciones lanza un proveedor real.
            return [
                AtributoPerfil(
                    nombre=NIVEL_INGRESOS_ESTIMADO,
                    valor=config.respaldo_nivel_ingresos_estimado,
                    origen=OrigenAdaptador.OPEN_FINANCE,
                    estado=EstadoAdaptador.DEGRADADO,
                    degradado=True,
                ),
                AtributoPerfil(
                    nombre=SCORE_COMPORTAMIENTO,
                    valor=config.respaldo_score_comportamiento,
                    origen=OrigenAdaptador.OPEN_FINANCE,
                    estado=EstadoAdaptador.DEGRADADO,
                    degradado=True,
                ),
            ]

    async def _invocar_open_data() -> list[AtributoPerfil]:
        try:
            datos = await asyncio.wait_for(
                adaptador_open_data.obtener_atributos(cliente_id),
                timeout=config.timeout_open_data_ms / 1000,
            )
            return [
                AtributoPerfil(
                    nombre=ZONA_RIESGO,
                    valor=datos[ZONA_RIESGO],
                    origen=OrigenAdaptador.OPEN_DATA,
                    estado=EstadoAdaptador.EXITO,
                    degradado=False,
                ),
                AtributoPerfil(
                    nombre=ANTIGUEDAD_DOCUMENTO,
                    valor=datos[ANTIGUEDAD_DOCUMENTO],
                    origen=OrigenAdaptador.OPEN_DATA,
                    estado=EstadoAdaptador.EXITO,
                    degradado=False,
                ),
            ]
        except Exception:
            return [
                AtributoPerfil(
                    nombre=ZONA_RIESGO,
                    valor=config.respaldo_zona_riesgo,
                    origen=OrigenAdaptador.OPEN_DATA,
                    estado=EstadoAdaptador.DEGRADADO,
                    degradado=True,
                ),
                AtributoPerfil(
                    nombre=ANTIGUEDAD_DOCUMENTO,
                    valor=config.respaldo_antiguedad_documento,
                    origen=OrigenAdaptador.OPEN_DATA,
                    estado=EstadoAdaptador.DEGRADADO,
                    degradado=True,
                ),
            ]

    atributos_open_finance, atributos_open_data = await asyncio.gather(
        _invocar_open_finance(), _invocar_open_data()
    )
    return [*atributos_open_finance, *atributos_open_data]


@dataclass(frozen=True)
class RegistroOferta:
    oferta: Oferta
    creada: bool


async def perfilar_y_ofertar(
    uow: FabricaUnidadDeTrabajo,
    adaptador_open_finance: AdaptadorOpenFinance,
    adaptador_open_data: AdaptadorOpenData,
    config: Settings,
    idempotency_key: str,
    cliente_id: str,
) -> RegistroOferta:
    """Orquesta HU-53+HU-54+HU-55+HU-56 en un único flujo (mismo endpoint/llamada):
    1) verifica consentimiento vigente (HU-53) ANTES de tocar cualquier adaptador;
    2) invoca los adaptadores con timeout, degradando con valor de respaldo si hace
       falta (HU-54/HU-56);
    3) arma el Perfil propio de Solventa (HU-55);
    4) calcula la Oferta explicable y la persiste junto con el snapshot completo de
       insumos, para que la decisión sea 100% reconstruible.
    """
    async with uow() as tx:
        existente = await tx.ofertas.obtener_por_clave(idempotency_key)
        if existente is not None:
            return RegistroOferta(existente, creada=False)

        vigente = await tx.consentimientos.obtener_vigente(cliente_id)
    if vigente is None:
        raise ConsentimientoNoOtorgado(cliente_id)

    atributos = await _atributos_con_respaldo(adaptador_open_finance, adaptador_open_data, cliente_id, config)
    perfil = Perfil.armar(cliente_id, atributos)
    pesos = {
        NIVEL_INGRESOS_ESTIMADO: config.peso_nivel_ingresos_estimado,
        SCORE_COMPORTAMIENTO: config.peso_score_comportamiento,
        ZONA_RIESGO: config.peso_zona_riesgo,
        ANTIGUEDAD_DOCUMENTO: config.peso_antiguedad_documento,
    }
    oferta = calcular_oferta(cliente_id, perfil, pesos, config.tarifa_base)

    async with uow() as tx:
        await tx.ofertas.agregar(idempotency_key, oferta)
        await tx.outbox.agregar(oferta_emitida(oferta))
        try:
            await tx.confirmar()
            return RegistroOferta(oferta, creada=True)
        except ClaveIdempotenciaDuplicada:
            pass

    async with uow() as tx:
        ganador = await tx.ofertas.obtener_por_clave(idempotency_key)
    if ganador is None:
        raise RuntimeError("Clave duplicada sin registro visible")
    return RegistroOferta(ganador, creada=False)


__all__ = [
    "RegistroConsentimiento",
    "RegistroOferta",
    "otorgar_consentimiento",
    "revocar_consentimiento",
    "consultar_consentimiento_vigente",
    "perfilar_y_ofertar",
]
