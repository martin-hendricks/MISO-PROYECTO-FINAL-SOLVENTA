package com.grupo8_uniandes.solventa.startup

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.session.MobileSessionRepository
import com.grupo8_uniandes.solventa.domain.bff.session.SessionTokens
import com.grupo8_uniandes.solventa.domain.profile.SessionRepository
import com.grupo8_uniandes.solventa.domain.startup.RestoreRemoteSession
import com.grupo8_uniandes.solventa.domain.startup.RestoredSession
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class RestoreRemoteSessionTest {
    @Test
    fun givenNoToken_whenRestore_thenTheLocalShellStays() = runTest {
        val remote = ScriptedSession(StandInAnswer.Failed)
        val local = RecordingSession()
        var cleared = false
        val result = restore(remote, local, token = null) { cleared = true }

        assertEquals(RestoredSession.Local, result)
        assertNull(remote.refreshToken)
        assertFalse(local.opened)
        assertFalse(local.closed)
        assertFalse(cleared)
    }

    @Test
    fun givenABlankToken_whenRestore_thenTheLocalShellStays() = runTest {
        val remote = ScriptedSession(StandInAnswer.Ready(sampleTokens()))
        val local = RecordingSession()
        val result = restore(remote, local, token = " ") { }

        assertEquals(RestoredSession.Local, result)
        assertNull(remote.refreshToken)
        assertFalse(local.opened)
    }

    @Test
    fun givenAReadyRefresh_whenRestore_thenHomeOpens() = runTest {
        val remote = ScriptedSession(StandInAnswer.Ready(sampleTokens()))
        val local = RecordingSession()
        var cleared = false
        val result = restore(remote, local, token = "refresh") { cleared = true }

        assertEquals(RestoredSession.Home, result)
        assertEquals("refresh", remote.refreshToken)
        assertTrue(local.opened)
        assertFalse(local.closed)
        assertFalse(cleared)
    }

    @Test
    fun givenAFailedRefresh_whenRestore_thenLoginClearsTheSession() = runTest {
        val remote = ScriptedSession(StandInAnswer.Failed)
        val local = RecordingSession()
        var cleared = false
        val result = restore(remote, local, token = "refresh") { cleared = true }

        assertEquals(RestoredSession.Login, result)
        assertEquals("refresh", remote.refreshToken)
        assertFalse(local.opened)
        assertTrue(local.closed)
        assertTrue(cleared)
    }

    @Test
    fun givenAPendingRefresh_whenRestore_thenLoginClearsTheSession() = runTest {
        val remote = ScriptedSession(StandInAnswer.Pending)
        val local = RecordingSession()
        var cleared = false
        val result = restore(remote, local, token = "refresh") { cleared = true }

        assertEquals(RestoredSession.Login, result)
        assertTrue(local.closed)
        assertTrue(cleared)
    }

    private suspend fun restore(
        remote: ScriptedSession,
        local: RecordingSession,
        token: String?,
        clear: () -> Unit,
    ) = RestoreRemoteSession(
        storedRefreshToken = { token },
        clearStoredSession = clear,
        remote = remote,
        local = local,
    )()

    private fun sampleTokens() = SessionTokens("access", "refresh", 900)

    private class ScriptedSession(
        private val answer: StandInAnswer<SessionTokens>,
    ) : MobileSessionRepository {
        var refreshToken: String? = null

        override suspend fun signIn(correo: String, contrasena: String): StandInAnswer<SessionTokens> =
            StandInAnswer.Failed

        override suspend fun refresh(refreshToken: String): StandInAnswer<SessionTokens> {
            this.refreshToken = refreshToken
            return answer
        }

        override suspend fun signOut(): StandInAnswer<Unit> = StandInAnswer.Failed
    }

    private class RecordingSession : SessionRepository {
        var opened = false
        var closed = false

        override fun isOpen(): Boolean = true

        override fun close() {
            closed = true
        }

        override fun open() {
            opened = true
        }
    }
}
