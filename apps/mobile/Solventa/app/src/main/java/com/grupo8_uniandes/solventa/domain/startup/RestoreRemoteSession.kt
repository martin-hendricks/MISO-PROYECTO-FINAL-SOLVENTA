package com.grupo8_uniandes.solventa.domain.startup

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.profile.SessionRepository

enum class RestoredSession {
    Local,
    Home,
    Login,
}

fun interface StoredRefreshToken {
    fun read(): String?
}

fun interface ClearStoredSession {
    fun clear()
}

/**
 * A stored refresh token is renewed before Home. No token keeps the local shell.
 * Anything other than a ready answer drops the stored pair and asks for login.
 */
class RestoreRemoteSession(
    private val storedRefreshToken: StoredRefreshToken,
    private val clearStoredSession: ClearStoredSession,
    private val remote: MobileSessionRepository,
    private val local: SessionRepository,
) {
    suspend operator fun invoke(): RestoredSession {
        val refresh = storedRefreshToken.read()
        if (refresh.isNullOrBlank()) return RestoredSession.Local
        return when (remote.refresh(refresh)) {
            is StandInAnswer.Ready -> {
                local.open()
                RestoredSession.Home
            }
            else -> {
                clearStoredSession.clear()
                local.close()
                RestoredSession.Login
            }
        }
    }
}
