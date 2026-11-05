package com.grupo8_uniandes.solventa.profile

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import com.grupo8_uniandes.solventa.domain.profile.SignOut
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
