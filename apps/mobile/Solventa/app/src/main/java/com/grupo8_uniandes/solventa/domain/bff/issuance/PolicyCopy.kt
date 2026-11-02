package com.grupo8_uniandes.solventa.domain.bff.issuance

import java.time.LocalDate
import java.time.format.DateTimeFormatter
import java.util.Locale

const val DEVICE_LINE = "Protección de dispositivo"

const val DEVICE_GUIDANCE =
    "Si se rompe la pantalla o te roban el equipo: toma la foto del daño, anota fecha y lugar, y no repares antes de dar el aviso. Cada ramo pide una evidencia distinta."

private val coverageDate: DateTimeFormatter =
    DateTimeFormatter.ofPattern("d MMM yyyy", Locale.forLanguageTag("es-CO"))

fun formatCoverageDate(isoDate: String): String =
    LocalDate.parse(isoDate).format(coverageDate).replace(".", "")

fun listBody(entry: WalletEntry): String = "${entry.ramo} · ${entry.resumen}"

fun listMeta(entry: WalletEntry): String = when (entry.estado) {
    "vigente" -> "Vigente · vence ${formatCoverageDate(entry.venceEn)}"
    "por_vencer" -> "Por vencer · en 7 días"
    else -> entry.estado
}

fun detailMeta(detail: PolicyDetail): String = when {
    detail.numero == "POL-88219-CO" && detail.estado == "vigente" ->
        "Vigente hasta ${formatCoverageDate(detail.venceEn)} · sigue renovación"
    detail.estado == "por_vencer" -> "Por vencer · en 7 días"
    detail.estado == "vigente" -> "Vigente · vence ${formatCoverageDate(detail.venceEn)}"
    else -> detail.estado
}

fun guidanceFor(detail: PolicyDetail): String =
    if (detail.ramo == DEVICE_LINE) detail.queHacer.ifBlank { DEVICE_GUIDANCE } else ""
