package com.grupo8_uniandes.solventa.login

import com.grupo8_uniandes.solventa.domain.login.SignIn
import com.grupo8_uniandes.solventa.domain.login.SignInResult
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class SignInTest {
    @Test
    fun givenSavedPair_whenTrimmedMatch_thenSignedInAndNothingIsWritten() {
        val repository = FakeRegistrationRepository(savedAccount())
        val signIn = SignIn(repository)

        val result = signIn.submit("  camila@correo.com  ", "  secret  ")

        assertEquals(SignInResult.SignedIn, result)
        assertEquals(0, repository.writes)
    }

    @Test
    fun givenDifferentCase_whenSubmitted_thenRejected() {
        val repository = FakeRegistrationRepository(savedAccount())

        val result = SignIn(repository).submit("Camila@correo.com", "secret")

        assertEquals(SignInResult.Rejected, result)
        assertEquals(0, repository.writes)
    }

    @Test
    fun givenDemoPair_whenNoRegistration_thenSignedInAndNothingIsWritten() {
        val repository = FakeRegistrationRepository(saved = null)

        val result = SignIn(repository).submit("  camila@correo.com  ", "  secret  ")

        assertEquals(SignInResult.SignedIn, result)
        assertEquals(0, repository.writes)
    }

    @Test
    fun givenNoRegistration_whenNotTheDemoPair_thenRejected() {
        val repository = FakeRegistrationRepository(saved = null)
        val signIn = SignIn(repository)

        assertEquals(SignInResult.Rejected, signIn.submit("camila@correo.com", "other"))
        assertEquals(SignInResult.Rejected, signIn.submit("other@correo.com", "secret"))
        assertEquals(SignInResult.Rejected, signIn.submit("Camila@correo.com", "secret"))
        assertEquals(0, repository.writes)
    }

    @Test
    fun givenWrongPassword_whenSubmitted_thenRejected() {
        val repository = FakeRegistrationRepository(savedAccount())

        val result = SignIn(repository).submit("camila@correo.com", "other")

        assertEquals(SignInResult.Rejected, result)
    }

    @Test
    fun givenBlankField_whenSubmitted_thenIncomplete() {
        val repository = FakeRegistrationRepository(savedAccount())
        val signIn = SignIn(repository)

        assertEquals(SignInResult.Incomplete, signIn.submit("", "secret"))
        assertEquals(SignInResult.Incomplete, signIn.submit("camila@correo.com", "   "))
        assertEquals(SignInResult.Incomplete, signIn.submit("  ", "  "))
        assertTrue(signIn.submit("camila@correo.com", "   ") != SignInResult.Rejected)
        assertEquals(0, repository.writes)
    }

    @Test
    fun givenMalformedEmail_whenItMatchesTheSavedValue_thenSignedIn() {
        val saved = savedAccount().copyEmail("not-an-email")
        val repository = FakeRegistrationRepository(saved)

        val result = SignIn(repository).submit("not-an-email", "secret")

        assertEquals(SignInResult.SignedIn, result)
    }
}

private fun savedAccount(): Registration = Registration(
    givenName = "Camila",
    surnames = "Restrepo",
    email = "camila@correo.com",
    documentType = "CC",
    documentNumber = "1023456789",
    password = "secret",
    documentPhoto = byteArrayOf(1),
)

private fun Registration.copyEmail(email: String): Registration = Registration(
    givenName = givenName,
    surnames = surnames,
    email = email,
    documentType = documentType,
    documentNumber = documentNumber,
    password = password,
    documentPhoto = documentPhoto,
)

private class FakeRegistrationRepository(
    private val saved: Registration?,
) : RegistrationRepository {
    var writes: Int = 0

    override fun read(): Registration? = saved

    override fun save(registration: Registration) {
        writes += 1
    }
}
