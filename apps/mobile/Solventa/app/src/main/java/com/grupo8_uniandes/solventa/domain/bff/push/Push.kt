package com.grupo8_uniandes.solventa.domain.bff.push

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

enum class PushType {
    PAGO_AUTOMATICO,
    VENCIMIENTO,
    RENOVACION,
    ESTADO_SINIESTRO,
}

enum class PushDestination {
    PARAMETRICO,
    AVISO_VENCIMIENTO,
    AVISO_RENOVACION,
    DETALLE_SINIESTRO,
}

data class PushRegistration(
    val token: String,
    val plataforma: String,
)

data class PushNotice(
    val tipo: PushType,
    val titulo: String,
    val cuerpo: String,
    val destino: PushDestination,
    val poliza: String,
)

interface PushRepository {
    fun register(registration: PushRegistration): StandInAnswer<PushRegistration>

    fun notice(): StandInAnswer<PushNotice>
}
