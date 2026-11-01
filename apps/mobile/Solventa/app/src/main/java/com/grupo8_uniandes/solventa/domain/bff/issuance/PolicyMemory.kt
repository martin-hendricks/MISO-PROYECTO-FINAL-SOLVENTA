package com.grupo8_uniandes.solventa.domain.bff.issuance

interface PolicyMemory {
    fun readWallet(): List<WalletEntry>?

    fun writeWallet(entries: List<WalletEntry>)

    fun readDetail(numero: String): PolicyDetail?

    fun writeDetail(detail: PolicyDetail)
}

class InMemoryPolicyStore : PolicyMemory {
    private var wallet: List<WalletEntry>? = null
    private val details = mutableMapOf<String, PolicyDetail>()

    override fun readWallet(): List<WalletEntry>? = wallet

    override fun writeWallet(entries: List<WalletEntry>) {
        wallet = entries
    }

    override fun readDetail(numero: String): PolicyDetail? = details[numero]

    override fun writeDetail(detail: PolicyDetail) {
        details[detail.numero] = detail
    }
}
