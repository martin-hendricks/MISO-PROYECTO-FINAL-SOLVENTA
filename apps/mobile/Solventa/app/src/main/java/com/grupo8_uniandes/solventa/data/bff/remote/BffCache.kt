package com.grupo8_uniandes.solventa.data.bff.remote

import android.content.Context
import com.grupo8_uniandes.solventa.data.bff.dto.CancellationDto
import com.grupo8_uniandes.solventa.data.bff.dto.ClaimNoticeDto
import com.grupo8_uniandes.solventa.data.bff.dto.CoverageDto
import com.grupo8_uniandes.solventa.data.bff.dto.DetailDto
import com.grupo8_uniandes.solventa.data.bff.mapping.bffJson
import com.grupo8_uniandes.solventa.data.bff.mapping.toDetail
import com.grupo8_uniandes.solventa.data.bff.mapping.toDto
import com.grupo8_uniandes.solventa.data.bff.mapping.toEntries
import com.grupo8_uniandes.solventa.data.bff.mapping.toNotice
import com.grupo8_uniandes.solventa.data.bff.mapping.toWallet
import com.grupo8_uniandes.solventa.domain.bff.billetera.DepositMemory
import com.grupo8_uniandes.solventa.domain.bff.billetera.StoredWallet
import com.grupo8_uniandes.solventa.domain.bff.billetera.Wallet
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimHold
import com.grupo8_uniandes.solventa.domain.bff.claim.ClaimNotice
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyDetail
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyMemory
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import kotlinx.serialization.Serializable
import kotlinx.serialization.SerializationException

data class PendingClaim(val key: String, val notice: ClaimNotice)

class BffCache(context: Context) {
    private val prefs = context.applicationContext.getSharedPreferences(FILE, Context.MODE_PRIVATE)

    fun readPolicies(): List<PolicyEntry>? {
        val raw = prefs.getString(POLICIES, null) ?: return null
        return try {
            bffJson.decodeFromString<com.grupo8_uniandes.solventa.data.bff.dto.PoliciesDto>(raw).toEntries()
        } catch (_: SerializationException) {
            null
        }
    }

    fun writePolicies(entries: List<PolicyEntry>) {
        prefs.edit().putString(POLICIES, bffJson.encodeToString(entries.toDto())).commit()
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

    fun readBilletera(): StoredWallet? {
        val raw = prefs.getString(BILLETERA, null) ?: return null
        return try {
            val stored = bffJson.decodeFromString<StoredBilletera>(raw)
            StoredWallet(stored.body.toWallet(), stored.savedAt)
        } catch (_: SerializationException) {
            null
        }
    }

    fun writeBilletera(wallet: Wallet, savedAt: String) {
        val kept = wallet.copy(movimientos = wallet.movimientos.takeLast(KEPT_MOVEMENTS))
        val stored = StoredBilletera(savedAt, kept.toDto())
        prefs.edit().putString(BILLETERA, bffJson.encodeToString(stored)).commit()
    }

    fun clear() {
        val editor = prefs.edit()
        snapshotKeys.forEach { editor.remove(it) }
        editor.clear().commit()
    }

    /** Drops policy, claim, detail, and billetera snapshots when another customer signs in. */
    fun retainOwner(uid: String?) {
        if (uid.isNullOrBlank()) return
        val previous = prefs.getString(OWNER, null)
        if (previous != null && previous != uid) clear()
        prefs.edit().putString(OWNER, uid).commit()
    }

    private companion object {
        const val FILE = "solventa.bff"
        const val POLICIES = "policies"
        const val CLAIM = "claim"
        const val DETAILS = "details"
        const val OWNER = "owner"
        const val BILLETERA = "billetera"
        const val KEPT_MOVEMENTS = 200
        val snapshotKeys = listOf(POLICIES, CLAIM, DETAILS, BILLETERA)
    }
}

class BffDepositMemory(private val cache: BffCache) : DepositMemory {
    override fun read(): StoredWallet? = cache.readBilletera()

    override fun write(wallet: Wallet, savedAt: String) = cache.writeBilletera(wallet, savedAt)
}

class CachedClaimHold(private val cache: BffCache) : ClaimHold {
    override fun keep(key: String, notice: ClaimNotice) {
        cache.writeClaim(PendingClaim(key, notice))
    }

    override fun readKey(): String? = cache.readClaim()?.key

    override fun clear() {
        cache.clearClaim()
    }
}

class BffPolicyMemory(private val cache: BffCache) : PolicyMemory {
    override fun readPolicies(): List<PolicyEntry>? = cache.readPolicies()

    override fun writePolicies(entries: List<PolicyEntry>) = cache.writePolicies(entries)

    override fun readDetail(numero: String): PolicyDetail? = cache.readDetail(numero)

    override fun writeDetail(detail: PolicyDetail) = cache.writeDetail(detail)
}

@Serializable
private data class StoredClaim(val key: String, val notice: ClaimNoticeDto)

@Serializable
private data class StoredBilletera(
    val savedAt: String,
    val body: com.grupo8_uniandes.solventa.data.bff.dto.BilleteraDto,
)

@Serializable
private data class StoredDetails(val items: List<DetailDto>)

private fun PolicyDetail.toStored() = DetailDto(
    numero = numero,
    ramo = ramo,
    resumen = resumen,
    estado = estado,
    venceEn = venceEn,
    queHacer = queHacer,
    inicioVigencia = inicioVigencia,
    finVigencia = finVigencia,
    moneda = moneda,
    primaTotal = primaTotal,
    coberturas = coberturas.map { CoverageDto(it.nombre, it.sumaAsegurada, it.deducible) },
    renovable = renovable,
    renovacionAutomatica = renovacionAutomatica,
    cancelacion = cancelacion?.let { CancellationDto(it.motivo, it.canceladaEn, it.devolucionEstimada) },
)
