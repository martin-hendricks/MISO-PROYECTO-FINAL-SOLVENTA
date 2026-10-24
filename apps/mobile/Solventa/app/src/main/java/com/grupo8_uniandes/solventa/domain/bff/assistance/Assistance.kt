package com.grupo8_uniandes.solventa.domain.bff.assistance

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

data class Provider(
    val id: String,
    val nombre: String,
    val distanciaKm: Double,
    val zona: String,
)

data class AssistanceRequest(
    val prestadorId: String,
    val lat: Double,
    val lng: Double,
    val poliza: String,
)

data class AssistanceResult(
    val asistenciaId: String,
    val estado: String,
)

interface AssistanceRepository {
    suspend fun providers(): StandInAnswer<List<Provider>>

    suspend fun request(body: AssistanceRequest): StandInAnswer<AssistanceResult>
}
