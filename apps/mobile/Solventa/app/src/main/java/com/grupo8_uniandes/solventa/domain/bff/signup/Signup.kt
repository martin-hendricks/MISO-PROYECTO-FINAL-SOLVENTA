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
    val contrasena: String = "",
    val tipoDocumento: String = "",
    val ingresosMensuales: String = "",
    val gastosMensuales: String = "",
)

data class ConsentRevocation(
    val habeasData: Boolean,
)

interface SignupRepository {
    suspend fun register(record: SignupRecord): StandInAnswer<SignupRecord>

    suspend fun revokeConsent(): StandInAnswer<ConsentRevocation>
}

enum class LivenessCheck {
    Passed,
    Failed,
    Unavailable,
}

interface LivenessRepository {
    suspend fun check(photo: ByteArray): LivenessCheck

    suspend fun record(result: Liveness): StandInAnswer<Liveness>
}
