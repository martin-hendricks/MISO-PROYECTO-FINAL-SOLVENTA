package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.domain.registration.EmailAddress
import com.grupo8_uniandes.solventa.domain.registration.EmailStatus
import org.junit.Assert.assertEquals
import org.junit.Test

class EmailAddressTest {
    @Test
    fun givenWellFormedAddress_whenJudged_thenValid() {
        assertEquals(EmailStatus.Valid, EmailAddress.status("camila@correo.com"))
        assertEquals(EmailStatus.Valid, EmailAddress.status("  a@b.co  "))
    }

    @Test
    fun givenBrokenAddress_whenJudged_thenInvalid() {
        listOf("camila", "camila@", "camila@correo", "a@b@c.com", "@correo.com", "a@.com", "a@b.").forEach { value ->
            assertEquals(value, EmailStatus.Invalid, EmailAddress.status(value))
        }
    }

    @Test
    fun givenBlank_whenJudged_thenMissing() {
        assertEquals(EmailStatus.Missing, EmailAddress.status(""))
        assertEquals(EmailStatus.Missing, EmailAddress.status("   "))
    }
}
