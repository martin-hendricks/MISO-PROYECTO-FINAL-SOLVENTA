package com.grupo8_uniandes.solventa.profile

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.push.PushRegistration
import com.grupo8_uniandes.solventa.domain.bff.push.PushRepository
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import com.grupo8_uniandes.solventa.domain.profile.SignOut
import com.grupo8_uniandes.solventa.domain.push.PushOptIn
import com.grupo8_uniandes.solventa.domain.push.PushOptInState
import com.grupo8_uniandes.solventa.domain.push.PushToken
import kotlinx.coroutines.runBlocking
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SignOutTest {
    @Test
    fun givenTheServerRejectsLogout_whenCompleted_thenTheLocalSessionStillCloses() = runBlocking {
        val session = MemorySession()
        val remote = FakeRemote(StandInAnswer.Failed)
        SignOut(session, remote).complete()

        assertEquals(1, remote.calls)
        assertEquals(1, session.closes)
        assertFalse(session.isOpen())
    }

    @Test
    fun givenARemoteLogout_whenCompleted_thenTheServerIsCalledBeforeTheLocalSessionCloses() = runBlocking {
        val session = MemorySession()
        val remote = FakeRemote(StandInAnswer.Ready(Unit))
        remote.onSignOut = { assertTrue(session.isOpen()) }
        SignOut(session, remote).complete()

        assertEquals(1, remote.calls)
        assertFalse(session.isOpen())
    }

    @Test
    fun givenARegisteredToken_whenCompleted_thenUnregisterHappensBeforeTheSessionCloses() = runBlocking {
        val session = MemorySession()
        val remote = FakeRemote(StandInAnswer.Ready(Unit))
        val push = RecordingPush()
        val optIn = PushOptIn(FixedToken("fcm-1"), push).apply { sdk = 33 }
        optIn.onSessionStarted()
        remote.onSignOut = {
            assertEquals(listOf("fcm-1"), push.removed)
            assertTrue(session.isOpen())
        }

        SignOut(session, remote, push, FixedToken("fcm-1"), optIn).complete()

        assertEquals(1, remote.calls)
        assertFalse(session.isOpen())
        assertEquals(PushOptInState.NoPreguntado, optIn.state)
    }

    @Test
    fun givenUnregisterFails_whenCompleted_thenTheLocalSessionStillCloses() = runBlocking {
        val session = MemorySession()
        val remote = FakeRemote(StandInAnswer.Ready(Unit))
        val push = RecordingPush(StandInAnswer.Failed)
        val optIn = PushOptIn(FixedToken("fcm-1"), push)

        SignOut(session, remote, push, FixedToken("fcm-1"), optIn).complete()

        assertEquals(listOf("fcm-1"), push.removed)
        assertEquals(1, remote.calls)
        assertFalse(session.isOpen())
        assertEquals(PushOptInState.NoPreguntado, optIn.state)
    }

    @Test
    fun givenUnregisterThrows_whenCompleted_thenTheLocalSessionStillCloses() = runBlocking {
        val session = MemorySession()
        val remote = FakeRemote(StandInAnswer.Ready(Unit))
        val push = RecordingPush(blowUp = true)

        SignOut(session, remote, push, FixedToken("fcm-1"), null).complete()

        assertEquals(1, remote.calls)
        assertFalse(session.isOpen())
    }
}

private class FixedToken(private val token: String?) : PushToken {
    override suspend fun current(): String? = token
}

private class RecordingPush(
    private val answer: StandInAnswer<Unit> = StandInAnswer.Ready(Unit),
    private val blowUp: Boolean = false,
) : PushRepository {
    val removed = mutableListOf<String>()

    override suspend fun register(registration: PushRegistration): StandInAnswer<PushRegistration> =
        StandInAnswer.Ready(registration)

    override suspend fun unregister(token: String): StandInAnswer<Unit> {
        if (blowUp) error("host down")
        removed += token
        return answer
    }
}

private class FakeRemote(private val answer: StandInAnswer<Unit>) : MobileSessionRepository {
    var calls = 0
    var onSignOut: () -> Unit = {}

    override suspend fun signIn(correo: String, contrasena: String): StandInAnswer<SessionTokens> =
        error("unused")

    override suspend fun refresh(refreshToken: String): StandInAnswer<SessionTokens> = error("unused")

    override suspend fun signOut(): StandInAnswer<Unit> {
        calls += 1
        onSignOut()
        return answer
    }
}
