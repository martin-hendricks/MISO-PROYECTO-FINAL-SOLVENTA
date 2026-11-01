package com.grupo8_uniandes.solventa.data.bff.remote

import android.content.Context
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.DetailDto
import com.grupo8_uniandes.solventa.data.bff.mapping.bffJson
import com.grupo8_uniandes.solventa.data.bff.mapping.toDetail
import com.grupo8_uniandes.solventa.data.bff.mapping.toDto
import com.grupo8_uniandes.solventa.data.bff.mapping.toEntries
import com.grupo8_uniandes.solventa.data.bff.mapping.toNotice
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyMemory
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerializationException

data class PendingClaim(val key: String, val notice: ClaimNotice)

class BffCache(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences(FILE, Context.MODE_PRIVATE)

    fun readWallet(): List<WalletEntry>? {
        val raw = prefs.getString(WALLET, null) ?: return null
        return try {
            bffJson.decodeFromString<com.grupo8_uniandes.solventa.data.bff.dto.WalletDto>(raw).toEntries()
        } catch (_: SerializationException) {
            null
        }
    }

    fun writeWallet(entries: List<WalletEntry>) {
        prefs.edit().putString(WALLET, bffJson.encodeToString(entries.toDto())).commit()
    }

    fun readDetail(numero: String): PolicyDetail? = readDetails()[numero]

    fun writeDetail(detail: PolicyDetail) {
        val stored = readDetails().toMutableMap()
        stored[detail.numero] = detail
        val payload = StoredDetails(stored.values.map { it.toStored() })
        prefs.edit().putString(DETAILS, bffJson.encodeToString(payload)).commit()
    }

    private fun readDetails(): Map<String, PolicyDetail> {
        val raw = prefs.getString(DETAILS, null) ?: return emptyMap()
        return try {
            bffJson.decodeFromString<StoredDetails>(raw).items
                .map { it.toDetail() }
                .associateBy { it.numero }
        } catch (_: SerializationException) {
            emptyMap()
        }
    }

    fun readClaim(): PendingClaim? {
        val raw = prefs.getString(CLAIM, null) ?: return null
        return try {
            val stored = bffJson.decodeFromString<StoredClaim>(raw)
            PendingClaim(stored.key, stored.notice.toNotice())
        } catch (_: SerializationException) {
            null
        }
    }

    fun writeClaim(claim: PendingClaim) {
        val stored = StoredClaim(claim.key, claim.notice.toDto())
        prefs.edit().putString(CLAIM, bffJson.encodeToString(stored)).commit()
    }

    fun clearClaim() {
        prefs.edit().remove(CLAIM).commit()
    }

    fun clear() {
        prefs.edit().clear().commit()
    }

    private companion object {
        const val FILE = "solventa.bff"
        const val WALLET = "wallet"
        const val CLAIM = "claim"
        const val DETAILS = "details"
    }
}

class BffPolicyMemory(private val cache: BffCache) : PolicyMemory {
    override fun readWallet(): List<WalletEntry>? = cache.readWallet()

    override fun writeWallet(entries: List<WalletEntry>) = cache.writeWallet(entries)

    override fun readDetail(numero: String): PolicyDetail? = cache.readDetail(numero)

    override fun writeDetail(detail: PolicyDetail) = cache.writeDetail(detail)
}

@Serializable
private data class StoredClaim(val key: String, val notice: ClaimNoticeDto)

@Serializable
private data class StoredDetails(val items: List<DetailDto>)

private fun PolicyDetail.toStored() = DetailDto(numero, ramo, resumen, estado, venceEn, queHacer)
