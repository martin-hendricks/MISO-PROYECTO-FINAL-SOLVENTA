package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.registration.AccountDraft
import com.grupo8_uniandes.solventa.domain.registration.RegisterAccount
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.ui.registration.OnboardingEffect
import com.grupo8_uniandes.solventa.ui.registration.OnboardingViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
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
        assertEquals(listOf("CC", "CE", "PA"), state.documentTypeOptions)
        assertEquals("", state.documentNumber)
        assertEquals("", state.password)
        assertEquals("", state.passwordConfirm)
        assertFalse(state.hasPhoto)
        assertFalse(state.emailError)
        assertFalse(state.habeasData)
        assertFalse(state.continuarEnabled)
        assertNull(state.effect)
    }

    @Test
    fun givenEveryFieldAndPhoto_whenHabeasDataIsOff_thenContinuarStaysDisabled() {
        viewModel.onGivenName("Camila")
        viewModel.onSurnames("Restrepo")
        viewModel.onEmail("camila@correo.com")
        viewModel.onDocumentType("CC")
        viewModel.onDocumentNumber("1023456789")
        viewModel.onPassword("secret12")
        viewModel.onPasswordConfirm("secret12")
        viewModel.attachPhoto(byteArrayOf(7, 8))

        assertFalse(viewModel.state.value.habeasData)
        assertFalse(viewModel.state.value.continuarEnabled)
        viewModel.continuar()
        assertNull(viewModel.state.value.effect)
    }

    @Test
    fun givenEveryFieldAndPhoto_whenContinuar_thenHomeHandoff() {
        fillValid()
        viewModel.attachPhoto(byteArrayOf(7, 8))

        assertTrue(viewModel.state.value.continuarEnabled)
        viewModel.continuar()

        assertEquals(OnboardingEffect.ContinueToLiveness, viewModel.state.value.effect)
        assertEquals(1, register.drafts.size)
        assertEquals(Region.Colombia, register.regions.single())
        assertTrue(byteArrayOf(7, 8).contentEquals(register.drafts.single().documentPhoto))
    }

    @Test
    fun givenMexico_whenOpened_thenAdultDocumentTypes() {
        val mexico = OnboardingViewModel(register, Region.Mexico)

        assertEquals(listOf("INE", "CURP", "PA"), mexico.state.value.documentTypeOptions)
    }

    @Test
    fun givenMinorDocument_whenChosen_thenContinuarStaysDisabled() {
        fillValid()
        viewModel.attachPhoto(byteArrayOf(1))
        viewModel.onDocumentType("TI")

        assertFalse(viewModel.state.value.continuarEnabled)
        viewModel.continuar()
        assertTrue(register.drafts.isEmpty())
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
        assertEquals("secret12", state.password)
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
    fun givenMatchingPassword_whenConfirmed_thenContinuarEnablesUntilTheyDiffer() {
        fillValid()
        viewModel.attachPhoto(byteArrayOf(1))
        viewModel.onPassword("secret123")
        viewModel.onPasswordConfirm("secret123")

        assertTrue(viewModel.state.value.continuarEnabled)
        assertTrue(viewModel.state.value.passwordMinMet)
        assertTrue(viewModel.state.value.passwordMaxMet)

        viewModel.onPassword("secret12")
        viewModel.onPasswordConfirm("secret13")

        assertFalse(viewModel.state.value.continuarEnabled)
        viewModel.continuar()
        assertTrue(register.drafts.isEmpty())
    }

    @Test
    fun givenAShortOrLongPassword_whenTyped_thenContinuarStaysDisabled() {
        fillValid()
        viewModel.attachPhoto(byteArrayOf(1))

        viewModel.onPassword("qwerty1")
        viewModel.onPasswordConfirm("qwerty1")

        assertFalse(viewModel.state.value.passwordMinMet)
        assertTrue(viewModel.state.value.passwordMaxMet)
        assertFalse(viewModel.state.value.continuarEnabled)

        val tooLong = "a".repeat(73)
        viewModel.onPassword(tooLong)
        viewModel.onPasswordConfirm(tooLong)

        assertTrue(viewModel.state.value.passwordMinMet)
        assertFalse(viewModel.state.value.passwordMaxMet)
        assertFalse(viewModel.state.value.continuarEnabled)
        viewModel.continuar()
        assertTrue(register.drafts.isEmpty())

        viewModel.onPassword("secret12")
        viewModel.onPasswordConfirm("secret12")

        assertTrue(viewModel.state.value.passwordMinMet)
        assertTrue(viewModel.state.value.passwordMaxMet)
        assertTrue(viewModel.state.value.continuarEnabled)
    }

    @Test
    fun givenEmptyPhoto_whenAttached_thenContinuarStaysDisabled() {
        fillValid()
        viewModel.attachPhoto(byteArrayOf())

        assertFalse(viewModel.state.value.hasPhoto)
        assertFalse(viewModel.state.value.continuarEnabled)
    }

    @Test
    fun givenSaveRejected_whenContinuar_thenEffectStaysEmpty() {
        val rejected = OnboardingViewModel(RejectingRegister())
        rejected.onGivenName("Camila")
        rejected.onSurnames("Restrepo")
        rejected.onEmail("camila@correo.com")
        rejected.onDocumentType("CC")
        rejected.onDocumentNumber("1023456789")
        rejected.onPassword("secret12")
        rejected.onPasswordConfirm("secret12")
        rejected.attachPhoto(byteArrayOf(1))

        rejected.continuar()

        assertNull(rejected.state.value.effect)
    }

    @Test
    fun givenLoginEffect_whenAFieldChanges_thenEffectClears() {
        viewModel.yaTengoCuenta()
        viewModel.onGivenName("Camila")

        assertNull(viewModel.state.value.effect)
        assertEquals("Camila", viewModel.state.value.givenName)
    }

    @Test
    fun givenPartialForm_whenYaTengoCuenta_thenLoginWithoutSave() {
        viewModel.onEmail("camila@correo.com")

        viewModel.yaTengoCuenta()

        assertEquals(OnboardingEffect.OpenLogin, viewModel.state.value.effect)
        assertTrue(register.drafts.isEmpty())
    }

    @Test
    fun givenDraft_whenLoginIsDismissed_thenEffectClearsAndFieldsStay() {
        viewModel.onGivenName("Camila")
        viewModel.dismissLogin()

        assertNull(viewModel.state.value.effect)
        assertEquals("Camila", viewModel.state.value.givenName)

        viewModel.yaTengoCuenta()
        viewModel.dismissLogin()

        assertNull(viewModel.state.value.effect)
        assertEquals("Camila", viewModel.state.value.givenName)
        assertTrue(register.drafts.isEmpty())
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenARemoteSession_whenIngresoSucceeds_thenLivenessContinues() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        try {
            var asked: Pair<String, String>? = null
            val remote = OnboardingViewModel(register, openRemoteSession = { email, password ->
                asked = email to password
                true
            })
            fill(remote)
            remote.attachPhoto(byteArrayOf(1))
            remote.continuar()
            assertEquals("camila@correo.com" to "secret12", asked)
            assertEquals(OnboardingEffect.ContinueToLiveness, remote.state.value.effect)
            assertFalse(remote.state.value.unavailable)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenARemoteSession_whenIngresoFails_thenTheUnavailableBannerStays() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        try {
            val remote = OnboardingViewModel(register, openRemoteSession = { _, _ -> false })
            fill(remote)
            remote.attachPhoto(byteArrayOf(1))
            remote.continuar()
            assertNull(remote.state.value.effect)
            assertTrue(remote.state.value.unavailable)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenARemoteSession_whenIngresoThrows_thenTheUnavailableBannerStays() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        try {
            val remote = OnboardingViewModel(register, openRemoteSession = { _, _ -> error("bff") })
            fill(remote)
            remote.attachPhoto(byteArrayOf(1))
            remote.continuar()
            assertNull(remote.state.value.effect)
            assertTrue(remote.state.value.unavailable)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenARemoteSession_whenRegistroSucceeds_thenIngresoFollows() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        try {
            val order = mutableListOf<String>()
            var recorded: AccountDraft? = null
            var habeasData = false
            val remote = OnboardingViewModel(
                register,
                openRemoteSession = { _, _ ->
                    order += "ingreso"
                    true
                },
                registerRemote = { draft, granted ->
                    order += "registro"
                    recorded = draft
                    habeasData = granted
                    true
                },
            )
            fill(remote)
            remote.attachPhoto(byteArrayOf(1))
            remote.continuar()
            assertEquals(listOf("registro", "ingreso"), order)
            assertTrue(habeasData)
            assertEquals("CC", recorded?.documentType)
            assertEquals("1023456789", recorded?.documentNumber)
            assertEquals("camila@correo.com", recorded?.email)
            assertEquals("secret12", recorded?.password)
            assertEquals(OnboardingEffect.ContinueToLiveness, remote.state.value.effect)
            assertFalse(remote.state.value.unavailable)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenARemoteSession_whenRegistroFails_thenIngresoIsNotCalled() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        try {
            var ingreso = false
            val remote = OnboardingViewModel(
                register,
                openRemoteSession = { _, _ ->
                    ingreso = true
                    true
                },
                registerRemote = { _, _ -> false },
            )
            fill(remote)
            remote.attachPhoto(byteArrayOf(1))
            remote.continuar()
            assertFalse(ingreso)
            assertNull(remote.state.value.effect)
            assertTrue(remote.state.value.unavailable)
        } finally {
            Dispatchers.resetMain()
        }
    }

    @OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
    @Test
    fun givenARemoteSessionInFlight_whenContinuarAgain_thenItSubmitsOnce() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        try {
            var calls = 0
            lateinit var remote: OnboardingViewModel
            remote = OnboardingViewModel(register, openRemoteSession = { _, _ ->
                calls += 1
                remote.continuar()
                true
            })
            fill(remote)
            remote.attachPhoto(byteArrayOf(1))
            remote.continuar()
            assertEquals(1, calls)
            assertEquals(OnboardingEffect.ContinueToLiveness, remote.state.value.effect)
        } finally {
            Dispatchers.resetMain()
        }
    }

    private fun fillValid() {
        fill(viewModel)
    }

    private fun fill(target: OnboardingViewModel) {
        target.onGivenName("Camila")
        target.onSurnames("Restrepo")
        target.onEmail("camila@correo.com")
        target.onDocumentType("CC")
        target.onDocumentNumber("1023456789")
        target.onPassword("secret12")
        target.onPasswordConfirm("secret12")
        target.onHabeasData(true)
    }
}

private class RejectingRegister : RegisterAccount(
    object : RegistrationRepository {
        override fun read(): Registration? = null

        override fun save(registration: Registration) = error("a rejected submit does not save")
    },
) {
    override fun submit(draft: AccountDraft, region: Region): Boolean = false
}

private class RecordingRegister : RegisterAccount(
    object : RegistrationRepository {
        override fun read(): Registration? = null

        override fun save(registration: Registration) = error("the view model fakes the use case")
    },
) {
    val drafts = mutableListOf<AccountDraft>()
    val regions = mutableListOf<Region>()

    override fun submit(draft: AccountDraft, region: Region): Boolean {
        drafts += draft
        regions += region
        return true
    }
}
