package com.grupo8_uniandes.solventa.profile

import com.grupo8_uniandes.solventa.domain.profile.SignOut
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class SignOutTest {
    @Test
    fun givenAnOpenSession_whenMissingKey_thenItStaysOpen() {
        val session = MemorySession()
        assertTrue(session.isOpen())
    }

    @Test
    fun givenSignOut_whenClosed_thenItIsClosedAndCanOpenAgain() {
        val session = MemorySession()
        SignOut(session)()
        assertFalse(session.isOpen())
        assertEquals(1, session.closes)
        session.open()
        assertTrue(session.isOpen())
    }
}
