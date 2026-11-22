package com.grupo8_uniandes.solventa.domain.bff.claim

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.issuance.IssuanceRepository
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import java.time.LocalDate

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

fun PolicyEntry.canReportClaim(today: LocalDate = LocalDate.now()): Boolean =
    canReportClaim(estado, venceEn, today)

fun String.canReportClaim(): Boolean =
    trim().lowercase() in claimReportStates

/** In force means vigente or por vencer, and the coverage end is today or later. */
fun canReportClaim(estado: String, venceEn: String, today: LocalDate = LocalDate.now()): Boolean {
    if (!estado.canReportClaim()) return false
    val end = runCatching { LocalDate.parse(venceEn.take(10)) }.getOrNull() ?: return true
    return !end.isBefore(today)
}

// ms-polizas answers VIGENTE. por_vencer is still in force. vencida and cancelada are not.
// A past fin_vigencia is expired even while the stored estado is still VIGENTE.
private val claimReportStates = setOf("vigente", "por_vencer")
