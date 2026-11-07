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
            wallet.value.filter { it.canReportClaim() }
        } else {
            emptyList()
        }
    }
}

fun WalletEntry.canReportClaim(): Boolean =
    estado.trim().lowercase() in claimReportStates

// ms-polizas answers VIGENTE. por_vencer is still in force. vencida and cancelada are not.
private val claimReportStates = setOf("vigente", "por_vencer")
