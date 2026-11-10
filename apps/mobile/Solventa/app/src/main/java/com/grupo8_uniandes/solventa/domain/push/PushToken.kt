package com.grupo8_uniandes.solventa.domain.push

interface PushToken {
    /** Identificador ya registrado. No vuelve a llamar a FCM. */
    suspend fun current(): String?

    /** Registra la instalación en FCM y devuelve su FID. */
    suspend fun link(): String? = current()
}
