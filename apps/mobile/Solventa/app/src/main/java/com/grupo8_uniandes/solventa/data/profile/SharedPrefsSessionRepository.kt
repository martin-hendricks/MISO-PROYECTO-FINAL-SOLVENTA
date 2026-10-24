package com.grupo8_uniandes.solventa.data.profile

import android.content.Context
import android.content.SharedPreferences
import com.grupo8_uniandes.solventa.domain.profile.SessionRepository

internal const val SessionPrefsFile = "session_prefs"
internal const val KeySessionOpen = "session_open"

class SharedPrefsSessionRepository(
    private val prefs: SharedPreferences,
) : SessionRepository {
    constructor(context: Context) : this(
        context.applicationContext.getSharedPreferences(SessionPrefsFile, Context.MODE_PRIVATE),
    )

    override fun isOpen(): Boolean = prefs.getBoolean(KeySessionOpen, true)

    override fun close() {
        prefs.edit().putBoolean(KeySessionOpen, false).commit()
    }

    override fun open() {
        prefs.edit().putBoolean(KeySessionOpen, true).commit()
    }
}
