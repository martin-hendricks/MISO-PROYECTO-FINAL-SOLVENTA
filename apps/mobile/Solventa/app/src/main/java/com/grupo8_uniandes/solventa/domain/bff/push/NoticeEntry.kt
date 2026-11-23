package com.grupo8_uniandes.solventa.domain.bff.push

enum class NoticeKind {
    PAGO_AUTOMATICO,
    VENCIMIENTO,
    RENOVACION,
    ESTADO_SINIESTRO,
}

enum class NoticeDestination {
    PARAMETRICO,
    AVISO_VENCIMIENTO,
    AVISO_RENOVACION,
    DETALLE_SINIESTRO,
}

data class NoticeEntry(
    val tipo: NoticeKind,
    val titulo: String,
    val cuerpo: String,
    val destino: NoticeDestination,
    val poliza: String,
)
