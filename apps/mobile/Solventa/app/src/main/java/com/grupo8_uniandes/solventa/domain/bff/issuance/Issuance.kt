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

data class PolicyEntry(
    val numero: String,
    val ramo: String,
    val resumen: String,
    val estado: String,
    val venceEn: String,
)

data class PolicyCoverage(
    val nombre: String,
    val sumaAsegurada: Double,
    val deducible: Double,
)

data class PolicyCancellation(
    val motivo: String?,
    val canceladaEn: String?,
    val devolucionEstimada: Double?,
)

data class PolicyDetail(
    val numero: String,
    val ramo: String,
    val resumen: String,
    val estado: String,
    val venceEn: String,
    val queHacer: String,
    val inicioVigencia: String? = null,
    val finVigencia: String? = null,
    val moneda: String = "",
    val primaTotal: Double? = null,
    val coberturas: List<PolicyCoverage> = emptyList(),
    val renovable: Boolean = false,
    val renovacionAutomatica: Boolean = false,
    val cancelacion: PolicyCancellation? = null,
)

interface IssuanceRepository {
    suspend fun accept(cotizacionId: String): StandInAnswer<IssuedPolicy>

    suspend fun rejected(): StandInAnswer<IssueRejection>

    suspend fun policies(): StandInAnswer<List<PolicyEntry>>

    suspend fun consentRevoked(): Boolean = false

    suspend fun detail(numero: String): StandInAnswer<PolicyDetail>
}
