package com.grupo8_uniandes.solventa.domain.bff.push

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

enum class PushType {
    POLIZA_EMITIDA,
    POLIZA_RENOVADA,
    POLIZA_MODIFICADA,
    POLIZA_CANCELADA,
    MENSAJE_OPERADOR,
    DESCONOCIDO,
}

enum class PushDestination {
    POLIZA_DETALLE,
    INICIO,
}

data class PushRegistration(
    val token: String,
    val plataforma: String,
)

interface PushRepository {
    suspend fun register(registration: PushRegistration): StandInAnswer<PushRegistration>

    suspend fun unregister(token: String): StandInAnswer<Unit>
}

fun pushTypeFrom(tipo: String?): PushType = when (tipo) {
    "poliza_emitida" -> PushType.POLIZA_EMITIDA
    "poliza_renovada" -> PushType.POLIZA_RENOVADA
    "poliza_modificada" -> PushType.POLIZA_MODIFICADA
    "poliza_cancelada" -> PushType.POLIZA_CANCELADA
    "mensaje_operador" -> PushType.MENSAJE_OPERADOR
    else -> PushType.DESCONOCIDO
}

fun pushDestinationFrom(destino: String?): PushDestination = when (destino) {
    "poliza-detalle" -> PushDestination.POLIZA_DETALLE
    else -> PushDestination.INICIO
}
