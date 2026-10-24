package com.grupo8_uniandes.solventa.domain.bff.mortgage

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

data class CreditProfile(
    val valor: Long,
    val plazoMeses: Int,
    val consentimientoPerfil: Boolean,
)

data class MortgageQuote(
    val ramo: String,
    val estado: String,
    val prima: Long,
    val moneda: String,
    val factores: List<String>,
    val degradada: Boolean,
)

interface MortgageRepository {
    fun offer(profile: CreditProfile): StandInAnswer<MortgageQuote>

    fun degraded(): StandInAnswer<MortgageQuote>
}
