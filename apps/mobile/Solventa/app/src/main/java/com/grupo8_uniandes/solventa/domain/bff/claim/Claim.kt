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
)

data class ClaimNotice(
    val poliza: String,
    val fechaHecho: String,
    val geo: GeoPoint?,
    val adjuntos: List<Attachment>,
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
)

interface ClaimRepository {
    fun notify(notice: ClaimNotice): StandInAnswer<ClaimReceipt>

    fun list(): StandInAnswer<List<ClaimSummary>>
}
