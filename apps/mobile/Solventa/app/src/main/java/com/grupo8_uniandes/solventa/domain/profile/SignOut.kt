package com.grupo8_uniandes.solventa.domain.profile

import com.grupo8_uniandes.solventa.domain.bff.push.PushRepository
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.push.PushOptIn
import com.grupo8_uniandes.solventa.domain.push.PushToken

class SignOut(
    private val session: SessionRepository,
    private val remote: MobileSessionRepository? = null,
    private val push: PushRepository? = null,
    private val tokens: PushToken? = null,
    private val optIn: PushOptIn? = null,
) {
    operator fun invoke() {
        optIn?.reset()
        session.close()
    }

    suspend fun complete() {
        try {
            unregisterQuietly()
            remote?.signOut()
        } finally {
            optIn?.reset()
            session.close()
        }
    }

    private suspend fun unregisterQuietly() {
        val repository = push ?: return
        val token = try {
            tokens?.current()
        } catch (_: Exception) {
            null
        }?.takeIf { it.isNotBlank() } ?: return
        try {
            repository.unregister(token)
        } catch (_: Exception) {
            // A failed deactivation still closes the session.
        }
    }
}
