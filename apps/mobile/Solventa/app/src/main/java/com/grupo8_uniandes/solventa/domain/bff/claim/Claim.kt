package com.grupo8_uniandes.solventa.domain.bff.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

enum class ClaimStatus {
    RECIBIDO,
    EN_EVALUACION,
    DECIDIDO,
    ENRUTADO,
    PAGADO,
}

enum class AttachmentKind {
    FOTO,
    VIDEO,
    RECIBO,
    SOPORTE,
}

data class GeoPoint(
    val lat: Double,
    val lng: Double,
    val precisionM: Int,
)

data class Attachment(
    val tipo: AttachmentKind,
    val nombre: String,
    val contentType: String = "application/octet-stream",
    val tamanoBytes: Long = 0,
)

data class ClaimNotice(
    val poliza: String,
    val fechaHecho: String,
    val geo: GeoPoint?,
    val adjuntos: List<Attachment>,
    val descripcion: String = "",
    val lugar: String = "",
)

data class ClaimReceipt(
    val siniestroId: String,
    val estado: ClaimStatus,
)

data class ClaimSummary(
    val siniestroId: String,
    val ramo: String,
    val resumen: String,
    val estado: ClaimStatus,
    val estadoTexto: String? = null,
    val id: String = siniestroId,
    val tipo: String = "asistido",
    val fecha: String? = null,
    val reserva: Double? = null,
    val moneda: String? = null,
    val poliza: String? = null,
    val resultado: String? = null,
) {
    fun whatHappened(): String = "$ramo · $resumen"

    fun statusWords(): String {
        if (estado == ClaimStatus.DECIDIDO && resultado == "aprobado") return "Aprobado"
        if (estado == ClaimStatus.DECIDIDO && resultado == "rechazado") return "Rechazado"
        return estadoTexto ?: when (estado) {
            ClaimStatus.RECIBIDO -> "Recibido"
            ClaimStatus.EN_EVALUACION -> "En evaluación"
            ClaimStatus.DECIDIDO -> "Decidido"
            ClaimStatus.ENRUTADO -> "Enrutado"
            ClaimStatus.PAGADO -> "Pagado"
        }
    }
}

data class ClaimEvidence(
    val nombre: String,
    val tipo: String,
    val contentType: String,
    val url: String,
)

data class ClaimHistory(val estado: String, val fecha: String, val estadoTexto: String = "")

data class ClaimPayment(val comprobante: String, val monto: Double, val moneda: String, val fecha: String)

data class ClaimDetail(
    val summary: ClaimSummary,
    val poliza: String?,
    val descripcion: String?,
    val lugar: String?,
    val geo: GeoPoint?,
    val motivo: String?,
    val evidencia: List<ClaimEvidence>,
    val historial: List<ClaimHistory>,
    val pago: ClaimPayment?,
    val umbral: String?,
) {
    fun storedPayment(): ParametricNotice? {
        val payment = pago ?: return null
        if (summary.tipo != "parametrico" || summary.estado != ClaimStatus.PAGADO) return null
        return ParametricNotice(
            asunto = summary.resumen,
            disparo = umbral.orEmpty(),
            monto = payment.monto.toLong(),
            moneda = payment.moneda,
            lineaDepositada = "${payment.monto.toLong()} ${payment.moneda}",
        )
    }
}

interface ClaimRepository {
    suspend fun notify(notice: ClaimNotice, idempotencyKey: String? = null): StandInAnswer<ClaimReceipt>

    suspend fun list(): StandInAnswer<List<ClaimSummary>>

    suspend fun detail(id: String): StandInAnswer<ClaimDetail> = StandInAnswer.Failed
}
