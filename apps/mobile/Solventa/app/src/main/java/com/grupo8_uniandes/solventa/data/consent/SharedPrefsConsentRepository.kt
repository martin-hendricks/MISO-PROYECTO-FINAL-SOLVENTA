package com.grupo8_uniandes.solventa.data.consent

import android.content.Context
import android.content.SharedPreferences
import com.grupo8_uniandes.solventa.domain.consent.ConsentAction
import com.grupo8_uniandes.solventa.domain.consent.ConsentRecord
import com.grupo8_uniandes.solventa.domain.consent.ConsentRepository
import com.grupo8_uniandes.solventa.domain.consent.ConsentSnapshot
import com.grupo8_uniandes.solventa.domain.consent.ConsentState

internal const val ConsentPrefsFile = "consent_prefs"
internal const val KeyConsentState = "state"
internal const val KeyConsentRecords = "records"

class SharedPrefsConsentRepository(
    private val prefs: SharedPreferences,
) : ConsentRepository {
    constructor(context: Context) : this(
        context.applicationContext.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE),
    )

    override fun read(): ConsentSnapshot {
        val records = parse(prefs.getString(KeyConsentRecords, "").orEmpty())
        val state = when (prefs.getString(KeyConsentState, null)) {
            "granted" -> ConsentState.Granted
            "revoked" -> ConsentState.Revoked
            else -> ConsentState.NotGranted
        }
        return ConsentSnapshot(state = state, records = records)
    }

    override fun append(record: ConsentRecord) {
        val current = read()
        val allowed = when (record.action) {
            ConsentAction.Grant ->
                current.state != ConsentState.Granted && record.resulting == ConsentState.Granted
            ConsentAction.Revoke ->
                current.state == ConsentState.Granted && record.resulting == ConsentState.Revoked
        }
        if (!allowed || current.state == record.resulting) return
        val line = record.toLine()
        val existing = prefs.getString(KeyConsentRecords, "").orEmpty()
        val next = if (existing.isEmpty()) line else "$existing\n$line"
        prefs.edit()
            .putString(KeyConsentState, record.resulting.toWire())
            .putString(KeyConsentRecords, next)
            .commit()
    }
}

private fun ConsentRecord.toLine(): String {
    val action = if (action == ConsentAction.Grant) "GRANT" else "REVOKE"
    return "$action|$atMillis|${resulting.toWire()}"
}

internal fun ConsentState.toWire(): String = when (this) {
    ConsentState.Granted -> "granted"
    ConsentState.Revoked -> "revoked"
    ConsentState.NotGranted -> "not_granted"
}

private fun parse(stored: String): List<ConsentRecord> {
    if (stored.isEmpty()) return emptyList()
    return stored.lineSequence().mapNotNull { line ->
        val parts = line.split('|')
        if (parts.size != 3) return@mapNotNull null
        val action = when (parts[0]) {
            "GRANT" -> ConsentAction.Grant
            "REVOKE" -> ConsentAction.Revoke
            else -> return@mapNotNull null
        }
        val atMillis = parts[1].toLongOrNull() ?: return@mapNotNull null
        val resulting = when (parts[2]) {
            "granted" -> ConsentState.Granted
            "revoked" -> ConsentState.Revoked
            else -> return@mapNotNull null
        }
        ConsentRecord(action = action, atMillis = atMillis, resulting = resulting)
    }.toList()
}
