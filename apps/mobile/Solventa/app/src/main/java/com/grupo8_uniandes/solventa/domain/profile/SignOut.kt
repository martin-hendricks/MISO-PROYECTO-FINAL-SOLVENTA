package com.grupo8_uniandes.solventa.domain.profile

class SignOut(
    private val session: SessionRepository,
) {
    operator fun invoke() {
        session.close()
    }
}
