package com.grupo8_uniandes.solventa.domain.push

import android.os.Build
import com.grupo8_uniandes.solventa.domain.bff.push.PushRegistration
import com.grupo8_uniandes.solventa.domain.bff.push.PushRepository

enum class PushOptInState {
    NoPreguntado,
    Preguntado,
}

sealed interface PushPrompt {
    data object Ask : PushPrompt

    data object Continue : PushPrompt
}

class PushOptIn(
    private val tokens: PushToken,
    private val push: PushRepository,
) {
    var state: PushOptInState = PushOptInState.NoPreguntado
        private set

    internal var sdk: Int = Build.VERSION.SDK_INT

    suspend fun onSessionStarted(): PushPrompt {
        if (sdk >= 33) {
            if (state == PushOptInState.Preguntado) return PushPrompt.Continue
            state = PushOptInState.Preguntado
            return PushPrompt.Ask
        }
        registerCurrent()
        return PushPrompt.Continue
    }

    suspend fun onPermissionResult(granted: Boolean) {
        if (granted) registerCurrent()
    }

    suspend fun onNewToken(token: String) {
        if (token.isBlank()) return
        push.register(PushRegistration(token, PLATFORM))
    }

    fun reset() {
        state = PushOptInState.NoPreguntado
    }

    private suspend fun registerCurrent() {
        val token = tokens.link()?.takeIf { it.isNotBlank() } ?: return
        push.register(PushRegistration(token, PLATFORM))
    }

    private companion object {
        const val PLATFORM = "android"
    }
}
