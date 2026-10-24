package com.grupo8_uniandes.solventa.domain.bff.issuance

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

data class IssuedPolicy(
    val numero: String,
    val ramo: String,
    val estado: String,
    val venceEn: String,
)

data class IssueRejection(
    val estado: String,
    val motivo: String,
)

data class WalletEntry(
    val numero: String,
    val ramo: String,
    val resumen: String,
    val estado: String,
    val venceEn: String,
)

data class PolicyDetail(
    val numero: String,
    val ramo: String,
    val resumen: String,
    val estado: String,
    val venceEn: String,
    val queHacer: String,
)

interface IssuanceRepository {
    suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy>

    suspend fun rejected(): StandInAnswer<IssueRejection>

    suspend fun wallet(): StandInAnswer<List<WalletEntry>>

    suspend fun detail(numero: String): StandInAnswer<PolicyDetail>
}
