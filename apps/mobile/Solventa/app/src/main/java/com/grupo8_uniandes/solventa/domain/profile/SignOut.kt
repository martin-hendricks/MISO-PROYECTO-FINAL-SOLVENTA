package com.grupo8_uniandes.solventa.domain.profile

import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository

class SignOut(
    private val session: SessionRepository,
    private val remote: MobileSessionRepository? = null,
) {
    operator fun invoke() {
        session.close()
    }

    suspend fun complete() {
        try {
            remote?.signOut()
        } finally {
            session.close()
        }
    }
}
