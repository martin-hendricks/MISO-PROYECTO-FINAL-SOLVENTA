package com.grupo8_uniandes.solventa.domain.bff.claim

interface LocalRenewal {
    fun read(poliza: String): Boolean

    fun write(poliza: String, enabled: Boolean)
}

class MemoryRenewal : LocalRenewal {
    private val values = mutableMapOf<String, Boolean>()

    override fun read(poliza: String): Boolean = values[poliza] == true

    override fun write(poliza: String, enabled: Boolean) {
        values[poliza] = enabled
    }
}
