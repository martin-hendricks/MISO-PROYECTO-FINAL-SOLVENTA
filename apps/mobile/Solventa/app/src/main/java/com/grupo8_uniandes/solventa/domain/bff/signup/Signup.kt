package com.grupo8_uniandes.solventa.domain.bff.signup

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer

enum class Liveness {
    OK,
    NO,
}

data class SignupRecord(
    val nombre: String,
    val apellidos: String,
    val documento: String,
    val correo: String,
    val pruebaDeVida: Liveness,
    val habeasData: Boolean,
)

data class ConsentRevocation(
    val habeasData: Boolean,
)

interface SignupRepository {
    suspend fun register(record: SignupRecord): StandInAnswer<SignupRecord>

    suspend fun revokeConsent(): StandInAnswer<ConsentRevocation>
}
