package com.grupo8_uniandes.solventa.domain.bff.issuance

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

data class PolicyListResult(
    val policies: List<WalletEntry>,
    val notice: Boolean,
    val empty: Boolean,
)

data class PolicyOpenResult(
    val detail: PolicyDetail?,
    val notice: Boolean,
    val missing: Boolean,
)

class ConsultPolicies(
    private val issuance: IssuanceRepository,
    private val memory: PolicyMemory,
) {
    private var staleList = false
    private val staleDetails = mutableSetOf<String>()

    suspend fun list(): PolicyListResult = when (val answer = issuance.wallet()) {
        is StandInAnswer.Ready -> {
            memory.writeWallet(answer.value)
            val notice = staleList
            staleList = false
            PolicyListResult(answer.value, notice = notice, empty = answer.value.isEmpty())
        }
        StandInAnswer.Failed -> {
            val saved = memory.readWallet()
            if (saved != null) {
                staleList = true
                PolicyListResult(saved, notice = false, empty = saved.isEmpty())
            } else {
                PolicyListResult(emptyList(), notice = false, empty = true)
            }
        }
        StandInAnswer.Pending -> PolicyListResult(emptyList(), notice = false, empty = false)
    }

    suspend fun open(numero: String): PolicyOpenResult = when (val answer = issuance.detail(numero)) {
        is StandInAnswer.Ready -> {
            val shown = reconcile(numero, answer.value)
            memory.writeDetail(shown)
            val notice = staleDetails.remove(numero)
            PolicyOpenResult(shown, notice = notice, missing = false)
        }
        StandInAnswer.Failed -> {
            val saved = memory.readDetail(numero)
            if (saved != null) {
                staleDetails += numero
                PolicyOpenResult(saved, notice = false, missing = false)
            } else {
                PolicyOpenResult(null, notice = false, missing = true)
            }
        }
        StandInAnswer.Pending -> PolicyOpenResult(null, notice = false, missing = false)
    }

    private fun reconcile(numero: String, detail: PolicyDetail): PolicyDetail {
        if (detail.numero != numero) {
            val entry = memory.readWallet()?.firstOrNull { it.numero == numero }
            if (entry != null) {
                return PolicyDetail(entry.numero, entry.ramo, entry.resumen, entry.estado, entry.venceEn, queHacer = "")
            }
        }
        val guidance = if (detail.ramo == DEVICE_LINE && detail.numero == numero) detail.queHacer else ""
        return detail.copy(numero = numero, queHacer = guidance)
    }
}
