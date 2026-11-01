package com.grupo8_uniandes.solventa.data.session

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens

/**
 * Access and refresh tokens for the mobile edge. Separate from region, consent, and registration.
 * Values in [FILE] are ciphertext. A plain open of that file does not yield the access credential.
 */
class TokenStore(context: Context) {
    private val prefs = encrypted(context.applicationContext)

    @Suppress("DEPRECATION")
    private fun encrypted(context: Context): SharedPreferences {
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        return EncryptedSharedPreferences.create(
            context,
            FILE,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
        )
    }

    fun read(): SessionTokens? {
        val access = prefs.getString(ACCESS, null) ?: return null
        val refresh = prefs.getString(REFRESH, null) ?: return null
        if (access.isBlank() || refresh.isBlank()) return null
        return SessionTokens(access, refresh, prefs.getInt(EXPIRES, 0))
    }

    fun save(tokens: SessionTokens) {
        prefs.edit()
            .putString(ACCESS, tokens.accessToken)
            .putString(REFRESH, tokens.refreshToken)
            .putInt(EXPIRES, tokens.expiraEn)
            .commit()
    }

    fun clear() {
        prefs.edit().clear().commit()
    }

    private companion object {
        const val FILE = "solventa.tokens"
        const val ACCESS = "accessToken"
        const val REFRESH = "refreshToken"
        const val EXPIRES = "expiraEn"
    }
}
