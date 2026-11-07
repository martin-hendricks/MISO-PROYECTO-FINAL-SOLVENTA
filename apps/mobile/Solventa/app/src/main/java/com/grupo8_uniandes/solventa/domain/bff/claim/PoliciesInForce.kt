package com.grupo8_uniandes.solventa.domain.bff.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry

class PoliciesInForce(
    private val issuance: IssuanceRepository,
) {
    suspend operator fun invoke(): List<WalletEntry> {
        val wallet = issuance.wallet()
        return if (wallet is StandInAnswer.Ready) {
            wallet.value.filter { it.estado.trim().lowercase() in inForce }
        } else {
            emptyList()
        }
    }

    private companion object {
        // ms-polizas answers VIGENTE. The mobile samples use vigente and por_vencer.
        val inForce = setOf("vigente", "por_vencer")
    }
}
