from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from decimal import Decimal

from app.config import Settings
from app.domain.errores import ConsentimientoNoOtorgado, NoEncontrado
from app.domain.modelos import (
    AtributoPerfil,
    CausaDegradacion,
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

_log = logging.getLogger(__name__)


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


async def revocar_consentimiento(uow: FabricaUnidadDeTrabajo, cliente_id: str, cache=None) -> Consentimiento:
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
    if cache is not None:
        await cache.invalidar_consentimiento(str(vigente.id))
    return vigente


async def consultar_consentimiento_vigente(uow: FabricaUnidadDeTrabajo, cliente_id: str) -> Consentimiento | None:
    async with uow() as tx:
        return await tx.consentimientos.obtener_vigente(cliente_id)


async def _atributos_con_respaldo(
    adaptador_open_finance: AdaptadorOpenFinance,
    adaptador_open_data: AdaptadorOpenData,
    cliente_id: str,
    config: Settings,
    cache=None,
    sujeto: str | None = None,
    consentimiento_id: str | None = None,
) -> list[AtributoPerfil]:
    """HU-54 + HU-56: invoca cada adaptador con su propio timeout (asyncio.wait_for).
    Si expira o el adaptador lanza cualquier excepción, sustituye por el valor de
    respaldo marcando degradado=True para ESE atributo. Nunca silencioso: el estado
    (éxito/degradado) queda explícito en cada AtributoPerfil, que luego se persiste
    como parte del resultado del perfilamiento."""

    sujeto_cache = sujeto or cliente_id

    async def _invocar(
        adaptador: AdaptadorOpenFinance | AdaptadorOpenData,
        origen: OrigenAdaptador,
        fuente: str,
        timeout_ms: int,
        respaldos: dict[str, Decimal],
    ) -> list[AtributoPerfil]:
        try:
            datos = await asyncio.wait_for(adaptador.obtener_atributos(sujeto_cache), timeout=timeout_ms / 1000)
            atributos = [
                AtributoPerfil(
                    nombre=nombre,
                    valor=datos[nombre],
                    origen=origen,
                    estado=EstadoAdaptador.EXITO,
                    degradado=False,
                )
                for nombre in respaldos
            ]
            if cache is not None:
                await cache.guardar(fuente, sujeto_cache, datos, consentimiento_id)
            return atributos
        except Exception as exc:
            # Ancho deliberado (igual que ms-cotizacion/app/application/casos_uso_cotizaciones.py):
            # el Gherkin de HU-56 exige degradar igual si el adaptador "excede su tiempo
            # límite o falla". La causa solo se registra para auditar cómo respondió.
            causa = CausaDegradacion.TIMEOUT if isinstance(exc, TimeoutError) else CausaDegradacion.FALLO
            entrada = await cache.obtener(fuente, sujeto_cache) if cache is not None else None
            if entrada is not None:
                return [
                    AtributoPerfil(
                        nombre=nombre,
                        valor=entrada.atributos[nombre],
                        origen=origen,
                        estado=EstadoAdaptador.EXITO,
                        degradado=False,
                        modo="CACHE",
                        causa=causa,
                    )
                    for nombre in respaldos
                ]
            _log.warning("adaptador %s degradado por %s", origen.value, causa.value)
            return [
                AtributoPerfil(
                    nombre=nombre,
                    valor=respaldo,
                    origen=origen,
                    estado=EstadoAdaptador.DEGRADADO,
                    degradado=True,
                    modo="DEFAULT",
                    causa=causa,
                )
                for nombre, respaldo in respaldos.items()
            ]

    atributos_open_finance, atributos_open_data = await asyncio.gather(
        _invocar(
            adaptador_open_finance,
            OrigenAdaptador.OPEN_FINANCE,
            "OPEN_FINANCE",
            config.timeout_open_finance_ms,
            {
                NIVEL_INGRESOS_ESTIMADO: config.respaldo_nivel_ingresos_estimado,
                SCORE_COMPORTAMIENTO: config.respaldo_score_comportamiento,
            },
        ),
        _invocar(
            adaptador_open_data,
            OrigenAdaptador.OPEN_DATA,
            "OPEN_DATA",
            config.timeout_open_data_ms,
            {
                ZONA_RIESGO: config.respaldo_zona_riesgo,
                ANTIGUEDAD_DOCUMENTO: config.respaldo_antiguedad_documento,
            },
        ),
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
    cache=None,
    numero_documento: str | None = None,
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

    atributos = await _atributos_con_respaldo(
        adaptador_open_finance,
        adaptador_open_data,
        cliente_id,
        config,
        cache=cache,
        sujeto=numero_documento,
        consentimiento_id=str(vigente.id),
    )
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
