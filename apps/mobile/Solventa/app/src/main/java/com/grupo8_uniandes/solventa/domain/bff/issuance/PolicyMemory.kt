package com.grupo8_uniandes.solventa.domain.bff.issuance

interface PolicyMemory {
    fun readPolicies(): List<PolicyEntry>?

    fun writePolicies(entries: List<PolicyEntry>)

    fun readDetail(numero: String): PolicyDetail?

    fun writeDetail(detail: PolicyDetail)
}

class InMemoryPolicyStore : PolicyMemory {
    private var wallet: List<PolicyEntry>? = null
    private val details = mutableMapOf<String, PolicyDetail>()

    override fun readPolicies(): List<PolicyEntry>? = wallet

    override fun writePolicies(entries: List<PolicyEntry>) {
        wallet = entries
    }

    override fun readDetail(numero: String): PolicyDetail? = details[numero]

    override fun writeDetail(detail: PolicyDetail) {
        details[detail.numero] = detail
    }
}
