package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.ui.registration.LivenessEffect
import com.grupo8_uniandes.solventa.ui.registration.LivenessViewModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class LivenessViewModelTest {
    @Test
    fun givenSavedAccount_whenOpened_thenFieldsArePrefilled() {
        val repository = MemoryRegistration(account())
        val viewModel = LivenessViewModel(repository, Region.Colombia)

        val state = viewModel.state.value
        assertEquals("Camila", state.givenName)
        assertEquals("Restrepo", state.surnames)
        assertEquals("camila@correo.com", state.email)
        assertEquals("CC", state.documentType)
        assertEquals("1023456789", state.documentNumber)
        assertEquals("secret", state.password)
        assertFalse(repository.liveness)
    }

    @Test
    fun givenSavedAccount_whenContinuar_thenAccountStaysAndConsentOpens() {
        val repository = MemoryRegistration(account())
        repository.choice = false
        val viewModel = LivenessViewModel(repository, Region.Colombia)
        viewModel.onGivenName("Ana")

        viewModel.continuar()

        assertEquals(LivenessEffect.OpenConsent, viewModel.state.value.effect)
        assertTrue(repository.liveness)
        assertEquals("Ana", repository.saved?.givenName)
        assertEquals("Restrepo", repository.saved?.surnames)
        assertTrue(byteArrayOf(1, 2).contentEquals(repository.saved?.documentPhoto))
        assertEquals(false, repository.choice)
    }

    @Test
    fun givenNoAccount_whenContinuar_thenLivenessStillOpensConsent() {
        val repository = MemoryRegistration(null)
        val viewModel = LivenessViewModel(repository)

        viewModel.continuar()

        assertEquals(LivenessEffect.OpenConsent, viewModel.state.value.effect)
        assertTrue(repository.liveness)
        assertEquals(null, repository.saved)
    }

    @Test
    fun givenScreen_whenYaTengoCuenta_thenLoginOpensAndDismissReturns() {
        val viewModel = LivenessViewModel(MemoryRegistration(account()))

        viewModel.dismissLogin()
        assertEquals(null, viewModel.state.value.effect)
        viewModel.onSurnames("Ruiz")
        viewModel.onEmail("ana@correo.com")
        viewModel.onDocumentType("CE")
        viewModel.onDocumentNumber("900")
        viewModel.onPassword("otra")
        viewModel.yaTengoCuenta()
        assertEquals(LivenessEffect.OpenLogin, viewModel.state.value.effect)
        viewModel.dismissLogin()
        assertEquals(null, viewModel.state.value.effect)
        assertEquals("Ruiz", viewModel.state.value.surnames)
        assertEquals("ana@correo.com", viewModel.state.value.email)
        assertEquals("CE", viewModel.state.value.documentType)
        assertEquals("900", viewModel.state.value.documentNumber)
        assertEquals("otra", viewModel.state.value.password)
    }
}

private fun account() = Registration(
    givenName = "Camila",
    surnames = "Restrepo",
    email = "camila@correo.com",
    documentType = "CC",
    documentNumber = "1023456789",
    password = "secret",
    documentPhoto = byteArrayOf(1, 2),
)

private class MemoryRegistration(
    initial: Registration?,
) : RegistrationRepository {
    var saved: Registration? = initial
    var liveness: Boolean = false
    var choice: Boolean? = null

    override fun read(): Registration? = saved

    override fun save(registration: Registration) {
        saved = registration
        choice = true
    }

    override fun update(registration: Registration) {
        saved = registration
    }

    override fun livenessCompleted(): Boolean = liveness

    override fun completeLiveness() {
        liveness = true
    }

    override fun biometricUnlockEnabled(): Boolean = choice == true

    override fun prefsChoiceExists(): Boolean = choice != null

    override fun setBiometricUnlock(enabled: Boolean) {
        choice = enabled
    }
}
