package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.domain.registration.AccountDraft
import com.grupo8_uniandes.solventa.domain.registration.RegisterAccount
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class RegisterAccountTest {
    private val repository = FakeRegistrationRepository()
    private val register = RegisterAccount(repository)

    @Test
    fun givenValidFormAndPhoto_whenSubmit_thenRegistrationIsStoredUnchanged() {
        val photo = byteArrayOf(1, 2, 3, 4)
        val saved = register.submit(
            draft(
                givenName = " Camila ",
                surnames = "Restrepo",
                email = " camila@correo.com ",
                documentType = "CC",
                documentNumber = "1023456789",
                password = "secret",
                documentPhoto = photo,
            ),
        )

        assertTrue(saved)
        val stored = repository.saved
        assertEquals("Camila", stored?.givenName)
        assertEquals("Restrepo", stored?.surnames)
        assertEquals("camila@correo.com", stored?.email)
        assertEquals("CC", stored?.documentType)
        assertEquals("1023456789", stored?.documentNumber)
        assertEquals("secret", stored?.password)
        assertTrue(photo.contentEquals(stored?.documentPhoto))
        assertFalse(stored?.email?.contains(photo.decodeToString()) == true)
    }

    @Test
    fun givenMissingOrInvalid_whenSubmit_thenNothingIsWritten() {
        val photo = byteArrayOf(9)
        assertFalse(register.submit(draft(givenName = "   ", documentPhoto = photo)))
        assertFalse(register.submit(draft(email = "camila", documentPhoto = photo)))
        assertFalse(register.submit(draft(password = " ", documentPhoto = photo)))
        assertFalse(register.submit(draft(documentPhoto = null)))
        assertFalse(register.submit(draft(documentPhoto = byteArrayOf())))
        assertNull(repository.saved)
    }

    private fun draft(
        givenName: String = "Camila",
        surnames: String = "Restrepo",
        email: String = "camila@correo.com",
        documentType: String = "CC",
        documentNumber: String = "1023456789",
        password: String = "secret",
        documentPhoto: ByteArray? = byteArrayOf(1),
    ) = AccountDraft(
        givenName = givenName,
        surnames = surnames,
        email = email,
        documentType = documentType,
        documentNumber = documentNumber,
        password = password,
        documentPhoto = documentPhoto,
    )
}

private class FakeRegistrationRepository : RegistrationRepository {
    var saved: Registration? = null

    override fun read(): Registration? = saved

    override fun save(registration: Registration) {
        saved = registration
    }
}
