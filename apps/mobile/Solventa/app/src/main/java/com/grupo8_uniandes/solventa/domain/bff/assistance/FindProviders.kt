package com.grupo8_uniandes.solventa.domain.bff.assistance

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

class FindProviders(
    private val assistance: AssistanceRepository,
) {
    private val remembered = linkedMapOf<String, Provider>()

    suspend fun search(query: ProviderQuery): StandInAnswer<ProviderPage> {
        val answer = assistance.providers(query)
        if (answer is StandInAnswer.Ready) {
            val ordered = answer.value.copy(prestadores = answer.value.prestadores.nearestFirst())
            remember(ordered.prestadores)
            return StandInAnswer.Ready(ordered)
        }
        return answer
    }

    suspend fun nearClaim(id: String): StandInAnswer<ClaimProviders> {
        val answer = assistance.providersNearClaim(id)
        if (answer is StandInAnswer.Ready) {
            val ordered = answer.value.copy(prestadores = answer.value.prestadores.nearestFirst())
            remember(ordered.prestadores)
            return StandInAnswer.Ready(ordered)
        }
        return answer
    }

    fun cached(id: String): Provider? = remembered[id]

    private fun remember(rows: List<Provider>) {
        rows.forEach { remembered[it.id] = it }
    }
}

private fun List<Provider>.nearestFirst(): List<Provider> =
    sortedBy { it.distanciaKm ?: Double.MAX_VALUE }
