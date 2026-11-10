package com.grupo8_uniandes.solventa.domain.bff.billetera

data class StoredWallet(val wallet: Wallet, val savedAt: String)

interface DepositMemory {
    fun read(): StoredWallet?
    fun write(wallet: Wallet, savedAt: String)
}

class InMemoryDepositStore : DepositMemory {
    private var stored: StoredWallet? = null

    override fun read(): StoredWallet? = stored

    override fun write(wallet: Wallet, savedAt: String) {
        stored = StoredWallet(wallet, savedAt)
    }
}
