package com.grupo8_uniandes.solventa.domain.bff.home

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

data class HomeOfferSlot(
    val cotizacionId: String,
    val ramo: String,
    val estado: String,
)

data class HomePolicySlot(
    val numero: String,
    val ramo: String,
    val estado: String,
)

data class HomeClaimSlot(
    val siniestroId: String,
    val estado: String,
)

data class BffHome(
    val ofertaVigente: HomeOfferSlot,
    val poliza: HomePolicySlot,
    val siniestroEnCurso: HomeClaimSlot,
    val hipotecario: String?,
)

interface HomeBffRepository {
    fun load(): StandInAnswer<BffHome>
}
