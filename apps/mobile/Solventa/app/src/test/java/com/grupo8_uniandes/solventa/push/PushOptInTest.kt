package com.grupo8_uniandes.solventa.push

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.push.PushRegistration
import com.grupo8_uniandes.solventa.domain.bff.push.PushRepository
import com.grupo8_uniandes.solventa.domain.push.PushOptIn
import com.grupo8_uniandes.solventa.domain.push.PushOptInState
import com.grupo8_uniandes.solventa.domain.push.PushPrompt
import com.grupo8_uniandes.solventa.domain.push.PushToken
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PushOptInTest {
    @Test
    fun givenApi33_whenTheSessionStarts_thenItAsksOnceUntilSignOut() = runBlocking {
        val push = RecordingPush()
        val optIn = optIn(push, sdk = 33)

        assertEquals(PushPrompt.Ask, optIn.onSessionStarted())
        assertEquals(PushOptInState.Preguntado, optIn.state)
        optIn.onPermissionResult(granted = false)
        assertTrue(push.registrations.isEmpty())
        assertEquals(PushPrompt.Continue, optIn.onSessionStarted())

        optIn.reset()
        assertEquals(PushOptInState.NoPreguntado, optIn.state)
        assertEquals(PushPrompt.Ask, optIn.onSessionStarted())
    }

    @Test
    fun givenApi33_whenPermissionIsGranted_thenTheTokenIsRegisteredForAndroid() = runBlocking {
        val push = RecordingPush()
        val optIn = optIn(push, sdk = 33, token = "fcm-1")

        assertEquals(PushPrompt.Ask, optIn.onSessionStarted())
        optIn.onPermissionResult(granted = true)

        assertEquals(listOf(PushRegistration("fcm-1", "android")), push.registrations)
    }

    @Test
    fun givenApi24To32_whenTheSessionStarts_thenItRegistersWithoutAsking() = runBlocking {
        listOf(24, 32).forEach { sdk ->
            val push = RecordingPush()
            val optIn = optIn(push, sdk = sdk, token = "fcm-$sdk")

            assertEquals(PushPrompt.Continue, optIn.onSessionStarted())
            assertEquals(PushOptInState.NoPreguntado, optIn.state)
            assertEquals(listOf(PushRegistration("fcm-$sdk", "android")), push.registrations)
        }
    }

    private fun optIn(push: RecordingPush, sdk: Int, token: String? = "fcm-1") =
        PushOptIn(FixedToken(token), push).apply { this.sdk = sdk }
}

private class FixedToken(private val token: String?) : PushToken {
    override suspend fun current(): String? = token
}

private class RecordingPush : PushRepository {
    val registrations = mutableListOf<PushRegistration>()

    override suspend fun register(registration: PushRegistration): StandInAnswer<PushRegistration> {
        registrations += registration
        return StandInAnswer.Ready(registration)
    }

    override suspend fun unregister(token: String): StandInAnswer<Unit> = StandInAnswer.Ready(Unit)
}
