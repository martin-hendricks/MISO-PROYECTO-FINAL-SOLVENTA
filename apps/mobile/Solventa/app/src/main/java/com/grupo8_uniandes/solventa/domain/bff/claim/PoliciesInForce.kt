package com.grupo8_uniandes.solventa.domain.bff.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry

class PoliciesInForce(
    private val issuance: IssuanceRepository,
) {
    suspend operator fun invoke(): List<PolicyEntry> {
        val wallet = issuance.policies()
        return if (wallet is StandInAnswer.Ready) {
            wallet.value.filter { it.canReportClaim() }
        } else {
            emptyList()
        }
    }
}

fun PolicyEntry.canReportClaim(): Boolean =
    estado.trim().lowercase() in claimReportStates

// ms-polizas answers VIGENTE. por_vencer is still in force. vencida and cancelada are not.
private val claimReportStates = setOf("vigente", "por_vencer")
