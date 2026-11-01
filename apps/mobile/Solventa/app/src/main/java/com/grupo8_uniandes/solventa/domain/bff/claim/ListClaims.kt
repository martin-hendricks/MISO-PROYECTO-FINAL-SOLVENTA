package com.grupo8_uniandes.solventa.domain.bff.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

class ListClaims(
    private val claims: ClaimRepository,
) {
    suspend operator fun invoke(): StandInAnswer<List<ClaimSummary>> = claims.list()
}
