package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.domain.registration.AccountDraft
import com.grupo8_uniandes.solventa.domain.registration.RegisterAccount
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.ui.registration.OnboardingEffect
import com.grupo8_uniandes.solventa.ui.registration.OnboardingViewModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class OnboardingViewModelTest {
    private val register = RecordingRegister()
    private val viewModel = OnboardingViewModel(register)

    @Test
    fun givenFreshForm_whenOpened_thenFieldsAreEmptyAndContinuarIsDisabled() {
        val state = viewModel.state.value

        assertEquals("", state.givenName)
        assertEquals("", state.surnames)
        assertEquals("", state.email)
        assertEquals("", state.documentType)
        assertEquals("", state.documentNumber)
        assertEquals("", state.password)
        assertFalse(state.hasPhoto)
        assertFalse(state.emailError)
        assertFalse(state.continuarEnabled)
        assertNull(state.effect)
    }

    @Test
    fun givenEveryFieldAndPhoto_whenContinuar_thenHomeHandoff() {
        fillValid()
        viewModel.attachPhoto(byteArrayOf(7, 8))

        assertTrue(viewModel.state.value.continuarEnabled)
        viewModel.continuar()

        assertEquals(OnboardingEffect.ContinueToHome, viewModel.state.value.effect)
        assertEquals(1, register.drafts.size)
        assertTrue(byteArrayOf(7, 8).contentEquals(register.drafts.single().documentPhoto))
    }

    @Test
    fun givenInvalidEmail_whenTyped_thenFieldIsMarkedAndOtherValuesStay() {
        fillValid()
        viewModel.onEmail("camila")

        val state = viewModel.state.value
        assertTrue(state.emailError)
        assertEquals("Camila", state.givenName)
        assertEquals("Restrepo", state.surnames)
        assertEquals("CC", state.documentType)
        assertEquals("1023456789", state.documentNumber)
        assertEquals("secret", state.password)
        assertFalse(state.continuarEnabled)
        viewModel.continuar()
        assertTrue(register.drafts.isEmpty())
        assertNull(viewModel.state.value.effect)
    }

    @Test
    fun givenSpacesOnly_whenContinuar_thenNothingIsSaved() {
        fillValid()
        viewModel.attachPhoto(byteArrayOf(1))
        viewModel.onPassword("   ")

        assertFalse(viewModel.state.value.continuarEnabled)
        assertFalse(viewModel.state.value.emailError)
        viewModel.continuar()
        assertTrue(register.drafts.isEmpty())
    }

    @Test
    fun givenEmptyEmail_whenJudged_thenNoErrorSentence() {
        viewModel.onEmail("   ")

        assertFalse(viewModel.state.value.emailError)
        assertFalse(viewModel.state.value.continuarEnabled)
    }

    @Test
    fun givenPhotoDeclined_whenReturned_thenTextStaysAndContinuarStaysDisabled() {
        fillValid()
        viewModel.attachPhoto(byteArrayOf(1))
        viewModel.photoDeclined()

        assertEquals("Camila", viewModel.state.value.givenName)
        assertFalse(viewModel.state.value.hasPhoto)
        assertFalse(viewModel.state.value.continuarEnabled)
        assertNull(viewModel.state.value.effect)
    }

    @Test
    fun givenPartialForm_whenYaTengoCuenta_thenLoginWithoutSave() {
        viewModel.onEmail("camila@correo.com")

        viewModel.yaTengoCuenta()

        assertEquals(OnboardingEffect.OpenLogin, viewModel.state.value.effect)
        assertTrue(register.drafts.isEmpty())
    }

    private fun fillValid() {
        viewModel.onGivenName("Camila")
        viewModel.onSurnames("Restrepo")
        viewModel.onEmail("camila@correo.com")
        viewModel.onDocumentType("CC")
        viewModel.onDocumentNumber("1023456789")
        viewModel.onPassword("secret")
    }
}

private class RecordingRegister : RegisterAccount(
    object : RegistrationRepository {
        override fun read(): Registration? = null

        override fun save(registration: Registration) = error("the view model fakes the use case")
    },
) {
    val drafts = mutableListOf<AccountDraft>()

    override fun submit(draft: AccountDraft): Boolean {
        drafts += draft
        return true
    }
}
