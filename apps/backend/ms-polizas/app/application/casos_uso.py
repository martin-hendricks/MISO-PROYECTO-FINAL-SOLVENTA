from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

from app.domain.errores import NoEncontrado, ReglaDeNegocioViolada
from app.domain.modelos import (
    VENTANA_GRACIA_DIAS,
    Cobertura,
    ConstanciaFirma,
    Poliza,
    numero_de_poliza,
    poliza_cancelada,
    poliza_emitida,
    poliza_modificada,
    poliza_por_vencer,
    poliza_renovada,
)
from app.ports.firma import FirmaElectronica
from app.ports.persistencia import FabricaUnidadDeTrabajo, PolizaYaEmitida
from app.ports.precondiciones import VerificadorCobro, VerificadorSuscripcion
from app.ports.reportes import GeneradorReportes, ReporteGenerado

# HU-119: ventana de aviso de vencimiento. Se reusa la misma constante que
# VENTANA_GRACIA_DIAS (30, HU-59) -- aunque conceptualmente son dos cosas
# distintas (avisar ANTES de vencer vs. tolerar renovar DESPUÉS de vencida),
# el mismo horizonte de 30 días es razonable para ambas y evita introducir un
# segundo número mágico que el Gherkin de notices.feature no especifica.
DIAS_AVISO_VENCIMIENTO_DEFECTO = VENTANA_GRACIA_DIAS


@dataclass(frozen=True)
class SolicitudEmision:
    solicitud_id: UUID
    oferta_id: UUID
    usuario_id: UUID
    token_pago_confirmado: UUID
    coberturas: list[Cobertura]


@dataclass(frozen=True)
class Emision:
    poliza: Poliza
    creada: bool


def _hoy() -> date:
    return datetime.now(UTC).date()


async def emitir_poliza(
    uow: FabricaUnidadDeTrabajo,
    suscripciones: VerificadorSuscripcion,
    cobros: VerificadorCobro,
    firma: FirmaElectronica,
    solicitud: SolicitudEmision,
) -> Emision:
    # Reintentar sobre la misma oferta devuelve la póliza ya emitida, sin volver a validar ni numerar.
    async with uow() as tx:
        existente = await tx.polizas.obtener_por_oferta(solicitud.oferta_id)
    if existente is not None:
        return Emision(existente, creada=False)

    if not await suscripciones.aceptada(solicitud.solicitud_id):
        raise ReglaDeNegocioViolada(
            "suscripcion_no_aceptada", "La póliza solo se emite sobre una suscripción aceptada"
        )
    if not await cobros.exitoso(solicitud.oferta_id, solicitud.token_pago_confirmado):
        raise ReglaDeNegocioViolada("cobro_no_exitoso", "La póliza solo se emite con el cobro de la prima exitoso")

    # HU-17: la constancia de firma se persiste siempre. Si la firma falla se
    # confirma sola y no se emite; si es exitosa viaja en la misma transacción
    # que la póliza, que guarda su hash.
    resultado = await firma.firmar(solicitud.oferta_id)
    constancia = ConstanciaFirma(
        oferta_id=solicitud.oferta_id,
        exitosa=resultado.exitosa,
        firmada_en=datetime.now(UTC),
        motivo=resultado.motivo,
        firma_hash=resultado.firma_hash,
    )
    if not resultado.exitosa:
        async with uow() as tx:
            await tx.firmas.agregar(constancia)
            await tx.confirmar()
        raise ReglaDeNegocioViolada("firma_no_exitosa", f"La firma electrónica no fue exitosa: {resultado.motivo}")

    async with uow() as tx:
        hoy = _hoy()
        numero = numero_de_poliza(hoy.year, await tx.polizas.siguiente_secuencia())
        poliza = Poliza.emitir(
            solicitud.oferta_id, solicitud.usuario_id, numero, solicitud.coberturas, hoy, resultado.firma_hash
        )
        await tx.firmas.agregar(constancia)
        await tx.polizas.agregar(poliza)
        await tx.outbox.agregar(poliza_emitida(poliza))
        try:
            await tx.confirmar()
            return Emision(poliza, creada=True)
        except PolizaYaEmitida:
            pass

    async with uow() as tx:
        ganadora = await tx.polizas.obtener_por_oferta(solicitud.oferta_id)
    if ganadora is None:
        raise RuntimeError("Oferta duplicada sin póliza visible")
    return Emision(ganadora, creada=False)


async def consultar_firma(uow: FabricaUnidadDeTrabajo, oferta_id: UUID) -> ConstanciaFirma:
    async with uow() as tx:
        constancia = await tx.firmas.ultima_por_oferta(oferta_id)
    if constancia is None:
        raise NoEncontrado(f"La oferta {oferta_id} no tiene constancia de firma")
    return constancia


async def consultar_poliza(uow: FabricaUnidadDeTrabajo, poliza_id: UUID) -> Poliza:
    async with uow() as tx:
        poliza = await tx.polizas.obtener(poliza_id)
    if poliza is None:
        raise NoEncontrado(f"La póliza {poliza_id} no existe")
    return poliza


async def consultar_poliza_por_numero(
    uow: FabricaUnidadDeTrabajo, numero: str, usuario_id: UUID | None = None
) -> Poliza:
    async with uow() as tx:
        poliza = await tx.polizas.obtener_por_numero(numero)
    if poliza is None or (usuario_id is not None and poliza.usuario_id != usuario_id):
        raise NoEncontrado(f"La póliza {numero} no existe")
    return poliza


async def listar_polizas_de_usuario(uow: FabricaUnidadDeTrabajo, usuario_id: UUID, limite: int) -> list[Poliza]:
    async with uow() as tx:
        return await tx.polizas.listar_por_usuario(usuario_id, limite)


async def ofertas_con_poliza(uow: FabricaUnidadDeTrabajo, oferta_ids: list[UUID]) -> list[UUID]:
    async with uow() as tx:
        encontradas = await tx.polizas.ofertas_con_poliza(oferta_ids)
    # Conserva el orden de la consulta para que la respuesta sea determinista.
    return [oferta_id for oferta_id in oferta_ids if oferta_id in encontradas]


async def _obtener_o_fallar(tx, poliza_id: UUID) -> Poliza:
    poliza = await tx.polizas.obtener(poliza_id)
    if poliza is None:
        raise NoEncontrado(f"La póliza {poliza_id} no existe")
    return poliza


async def renovar_poliza(uow: FabricaUnidadDeTrabajo, poliza_id: UUID, nueva_fin_vigencia: date) -> Poliza:
    """HU-59: extiende la vigencia. Lanza NoEncontrado si la póliza no existe
    y TransicionInvalida (vía Poliza.renovar) si no está VIGENTE ni dentro de
    la ventana de gracia tras vencer."""
    async with uow() as tx:
        poliza = await _obtener_o_fallar(tx, poliza_id)
        poliza.renovar(nueva_fin_vigencia, _hoy())
        await tx.polizas.actualizar(poliza)
        await tx.outbox.agregar(poliza_renovada(poliza))
        await tx.confirmar()
        return poliza


async def modificar_poliza(uow: FabricaUnidadDeTrabajo, poliza_id: UUID, nuevas_coberturas: list[Cobertura]) -> Poliza:
    """HU-60: reemplaza las coberturas. Lanza NoEncontrado si la póliza no
    existe y TransicionInvalida/ReglaDeNegocioViolada (vía
    Poliza.modificar_coberturas) si no está VIGENTE o las coberturas son inválidas."""
    async with uow() as tx:
        poliza = await _obtener_o_fallar(tx, poliza_id)
        poliza.modificar_coberturas(nuevas_coberturas)
        await tx.polizas.actualizar(poliza)
        await tx.outbox.agregar(poliza_modificada(poliza))
        await tx.confirmar()
        return poliza


async def guardar_renovacion_automatica(
    uow: FabricaUnidadDeTrabajo, poliza_id: UUID, valor: bool, usuario_id: UUID | None = None
) -> Poliza:
    """Persiste la preferencia del cliente. No cobra ni renueva la póliza."""
    async with uow() as tx:
        poliza = await _obtener_o_fallar(tx, poliza_id)
        if usuario_id is not None and poliza.usuario_id != usuario_id:
            raise NoEncontrado(f"La póliza {poliza_id} no existe")
        poliza.fijar_renovacion_automatica(valor, datetime.now(UTC))
        await tx.polizas.actualizar(poliza)
        await tx.confirmar()
        return poliza


async def cancelar_poliza(uow: FabricaUnidadDeTrabajo, poliza_id: UUID, motivo: str, cancelada_por: str) -> Poliza:
    """HU-61: única transición de estado real del ciclo de vida. Lanza
    NoEncontrado si la póliza no existe y TransicionInvalida (vía
    Poliza.cancelar) si ya estaba cancelada."""
    async with uow() as tx:
        poliza = await _obtener_o_fallar(tx, poliza_id)
        poliza.cancelar(motivo, _hoy(), cancelada_por)
        await tx.polizas.actualizar(poliza)
        await tx.outbox.agregar(poliza_cancelada(poliza))
        await tx.confirmar()
        return poliza


async def listar_polizas_por_vencer(
    uow: FabricaUnidadDeTrabajo,
    usuario_id: UUID | None = None,
    dias: int = DIAS_AVISO_VENCIMIENTO_DEFECTO,
) -> list[Poliza]:
    """HU-119: pólizas VIGENTE cuya fin_vigencia cae en los próximos `dias`
    días desde hoy (incluido). `usuario_id=None` lista de todos los
    usuarios -- uso reservado a asesor/operador (ver alcance() en seguridad.py)."""
    hoy = _hoy()
    async with uow() as tx:
        return await tx.polizas.listar_por_vencer(hoy, hoy + timedelta(days=dias), usuario_id)


async def generar_avisos_vencimiento(
    uow: FabricaUnidadDeTrabajo, dias: int = DIAS_AVISO_VENCIMIENTO_DEFECTO
) -> int:
    """HU-67: orquestador de ciclo de vida -- job periódico (ver
    app/jobs/avisos_vencimiento.py) que cierra el loop ms-polizas ->
    outbox-relay -> notificaciones sin que nadie llame GET /v1/polizas/
    por-vencer a mano. Reusa listar_polizas_por_vencer (HU-119) en vez de
    duplicar la query.

    Idempotente por póliza: si ya existe un evento "PolizaPorVencer" para
    esa póliza en el outbox (de una corrida anterior), no genera otro. Sin
    esto, correr el job a diario mientras la póliza sigue dentro de la
    ventana de `dias` generaría un push nuevo cada día -- notificaciones
    solo deduplica por (evento_origen_id, canal), y cada evento nuevo trae
    un evento_origen_id distinto, así que sí despacharía un push repetido.
    """
    generados = 0
    async with uow() as tx:
        por_vencer = await tx.polizas.listar_por_vencer(_hoy(), _hoy() + timedelta(days=dias))
        for poliza in por_vencer:
            if await tx.outbox.existe_para_agregado("PolizaPorVencer", poliza.id):
                continue
            await tx.outbox.agregar(poliza_por_vencer(poliza))
            generados += 1
        await tx.confirmar()
    return generados


async def generar_reporte_regulador(
    uow: FabricaUnidadDeTrabajo, reportes: GeneradorReportes, desde: date, hasta: date
) -> ReporteGenerado:
    """HU-62: extracto interno de pólizas emitidas en el rango para el
    regulador. El núcleo solo reúne los datos; el adaptador decide el
    formato del archivo (nunca SFC real)."""
    async with uow() as tx:
        polizas = await tx.polizas.listar_emitidas_entre(desde, hasta)
    return await reportes.reporte_regulador(polizas, desde, hasta)


async def generar_reporte_reaseguradora(
    uow: FabricaUnidadDeTrabajo, reportes: GeneradorReportes, desde: date, hasta: date
) -> ReporteGenerado:
    """HU-63: extracto de cartera (pólizas canceladas, con su devolución
    estimada) en el rango para la reaseguradora. El adaptador decide el
    formato del archivo (nunca ACORD real)."""
    async with uow() as tx:
        canceladas = await tx.polizas.listar_canceladas_entre(desde, hasta)
    return await reportes.reporte_reaseguradora(canceladas, desde, hasta)
