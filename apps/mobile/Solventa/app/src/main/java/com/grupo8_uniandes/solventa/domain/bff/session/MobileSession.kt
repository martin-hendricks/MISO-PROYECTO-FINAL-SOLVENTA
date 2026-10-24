package com.grupo8_uniandes.solventa.domain.bff.session

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

data class SessionTokens(
    val accessToken: String,
    val refreshToken: String,
    val expiraEn: Int,
)

interface MobileSessionRepository {
    fun signIn(correo: String, contrasena: String): StandInAnswer<SessionTokens>

    fun refresh(refreshToken: String): StandInAnswer<SessionTokens>

    fun signOut(): StandInAnswer<Unit>
}
