package com.grupo8_uniandes.solventa.registration

import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.signup.Liveness
import com.grupo8_uniandes.solventa.domain.bff.signup.LivenessCheck
import com.grupo8_uniandes.solventa.domain.bff.signup.LivenessRepository
import com.grupo8_uniandes.solventa.domain.bff.signup.VerifySelfie
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.registration.Registration
import com.grupo8_uniandes.solventa.domain.registration.RegistrationRepository
import com.grupo8_uniandes.solventa.ui.registration.LivenessEffect
import com.grupo8_uniandes.solventa.ui.registration.LivenessPhase
import com.grupo8_uniandes.solventa.ui.registration.LivenessViewModel
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TestWatcher
import org.junit.runner.Description

class LivenessViewModelTest {
    @get:Rule
    val mainDispatcher = object : TestWatcher() {
        override fun starting(description: Description) {
            Dispatchers.setMain(UnconfinedTestDispatcher())
        }

        override fun finished(description: Description) {
            Dispatchers.resetMain()
        }
    }

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

        assertEquals(LivenessPhase.Camera, viewModel.state.value.phase)
        assertEquals(null, viewModel.state.value.effect)
        assertFalse(repository.liveness)
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

        assertEquals(LivenessPhase.Camera, viewModel.state.value.phase)
        assertFalse(repository.liveness)
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

    @Test
    fun givenTheForm_whenContinuar_thenCameraOpensWithoutCompletingLiveness() {
        val repository = MemoryRegistration(account())
        val viewModel = LivenessViewModel(repository, verifySelfie = VerifySelfie(GateLiveness()))
        viewModel.continuar()
        assertEquals(LivenessPhase.Camera, viewModel.state.value.phase)
        assertFalse(repository.liveness)
    }

    @Test
    fun givenNoPermission_whenShutter_thenCameraIsRequested() {
        val viewModel = model()
        viewModel.continuar()
        viewModel.onShutter(cameraGranted = false)
        assertEquals(LivenessEffect.RequestCamera, viewModel.state.value.effect)
        viewModel.consumeEffect()
        assertNull(viewModel.state.value.effect)
    }

    @Test
    fun givenPermissionAlreadyGranted_whenShutter_thenACaptureIsRequested() {
        val viewModel = model()
        viewModel.continuar()
        viewModel.onShutter(cameraGranted = true)
        assertEquals(1, viewModel.state.value.captureTicket)
        viewModel.onShutter(cameraGranted = true)
        assertEquals(2, viewModel.state.value.captureTicket)
    }

    @Test
    fun givenTheForm_whenShutterIsGranted_thenNothingIsCaptured() {
        val viewModel = model()
        viewModel.onShutter(cameraGranted = true)
        assertEquals(0, viewModel.state.value.captureTicket)
        assertEquals(LivenessPhase.Form, viewModel.state.value.phase)
    }

    @Test
    fun givenPermissionGranted_whenPhotoPasses_thenPassedAndContinuarOpensHome() {
        val repository = MemoryRegistration(account())
        val gate = GateLiveness()
        val viewModel = LivenessViewModel(repository, verifySelfie = VerifySelfie(gate))
        viewModel.continuar()
        viewModel.onCameraResult(true)
        assertEquals(LivenessPhase.Camera, viewModel.state.value.phase)
        viewModel.onPhoto(byteArrayOf(9))
        assertEquals(LivenessPhase.Passed, viewModel.state.value.phase)
        viewModel.onPhoto(byteArrayOf(8))
        assertEquals(1, gate.checks)
        viewModel.continuarCamara()
        assertTrue(repository.liveness)
        assertEquals(LivenessEffect.OpenHome, viewModel.state.value.effect)
        assertNull(viewModel.state.value.photo)
    }

    @Test
    fun givenSending_whenAnotherPhotoArrives_thenItIsIgnored() {
        val gate = GateLiveness()
        val viewModel = model(gate)
        viewModel.continuar()
        viewModel.onPhoto(byteArrayOf(1))
        val checks = gate.checks
        viewModel.onPhoto(byteArrayOf(2))
        assertEquals(checks, gate.checks)
    }

    @Test
    fun givenCamera_whenBack_thenFormReturnsAndThePhotoIsCleared() {
        val viewModel = model()
        viewModel.continuar()
        viewModel.onPhoto(byteArrayOf(1))
        viewModel.back()
        assertEquals(LivenessPhase.Form, viewModel.state.value.phase)
        assertNull(viewModel.state.value.photo)
    }

    @Test
    fun givenAFailedCheck_whenRepeat_thenCameraReturns() {
        val gate = GateLiveness().also { it.checkResult = LivenessCheck.Failed }
        val viewModel = model(gate)
        viewModel.continuar()
        viewModel.onPhoto(byteArrayOf(1))
        assertEquals(LivenessPhase.Failed, viewModel.state.value.phase)
        viewModel.repetirFoto()
        assertEquals(LivenessPhase.Camera, viewModel.state.value.phase)
    }

    @Test
    fun givenDenied_whenRepeat_thenCameraIsRequestedAgain() {
        val viewModel = model()
        viewModel.continuar()
        viewModel.onCameraResult(false)
        assertEquals(LivenessPhase.Denied, viewModel.state.value.phase)
        viewModel.repetirFoto()
        assertEquals(LivenessEffect.RequestCamera, viewModel.state.value.effect)
    }

    @Test
    fun givenNoFrontCamera_whenUnavailable_thenDenied() {
        val viewModel = model()
        viewModel.continuar()
        viewModel.onCameraUnavailable()
        assertEquals(LivenessPhase.Denied, viewModel.state.value.phase)
    }

    @Test
    fun givenCheckUnavailable_whenRetry_thenTheSamePhotoIsSent() {
        val gate = GateLiveness().also { it.checkResult = LivenessCheck.Unavailable }
        val viewModel = model(gate)
        viewModel.continuar()
        viewModel.onPhoto(byteArrayOf(4, 5))
        assertEquals(LivenessPhase.Unavailable, viewModel.state.value.phase)
        gate.checkResult = LivenessCheck.Passed
        viewModel.reintentar()
        assertEquals(LivenessPhase.Passed, viewModel.state.value.phase)
        assertTrue(byteArrayOf(4, 5).contentEquals(gate.last))
        assertEquals(2, gate.checks)
    }

    @Test
    fun givenRecordUnavailable_whenRetry_thenOnlyTheRecordIsRetried() {
        val gate = GateLiveness().also { it.recordResult = StandInAnswer.Failed }
        val viewModel = model(gate)
        viewModel.continuar()
        viewModel.onPhoto(byteArrayOf(1))
        assertEquals(LivenessPhase.Unavailable, viewModel.state.value.phase)
        gate.recordResult = StandInAnswer.Ready(Liveness.OK)
        val checks = gate.checks
        viewModel.reintentar()
        assertEquals(checks, gate.checks)
        assertEquals(LivenessPhase.Passed, viewModel.state.value.phase)
    }

    @Test
    fun givenAnyBlockedState_whenContinueWithDocument_thenHomeOpensWithoutRecording() {
        val gate = GateLiveness().also { it.checkResult = LivenessCheck.Failed }
        val repository = MemoryRegistration(account())
        val viewModel = LivenessViewModel(repository, verifySelfie = VerifySelfie(gate))
        viewModel.continuar()
        viewModel.onPhoto(byteArrayOf(1))
        viewModel.continuarConDocumento()
        assertEquals(LivenessEffect.OpenHome, viewModel.state.value.effect)
        assertTrue(repository.liveness)
        assertEquals(0, gate.records)
        assertNull(viewModel.state.value.photo)
    }

    @Test
    fun givenAPhotoInFlight_whenYaTengoCuenta_thenLoginOpensAndALateResultIsIgnored() {
        val gate = GateLiveness()
        val viewModel = model(gate)
        viewModel.continuar()
        viewModel.yaTengoCuenta()
        assertEquals(LivenessEffect.OpenLogin, viewModel.state.value.effect)
        viewModel.onPhoto(byteArrayOf(1))
        assertEquals(LivenessEffect.OpenLogin, viewModel.state.value.effect)
        assertEquals(LivenessPhase.Camera, viewModel.state.value.phase)
    }
}

private fun model(gate: GateLiveness = GateLiveness()) =
    LivenessViewModel(MemoryRegistration(account()), verifySelfie = VerifySelfie(gate))

private class GateLiveness : LivenessRepository {
    var checkResult: LivenessCheck = LivenessCheck.Passed
    var recordResult: StandInAnswer<Liveness> = StandInAnswer.Ready(Liveness.OK)
    var checks: Int = 0
    var records: Int = 0
    var last: ByteArray? = null

    override suspend fun check(photo: ByteArray): LivenessCheck {
        checks += 1
        last = photo
        return checkResult
    }

    override suspend fun record(result: Liveness): StandInAnswer<Liveness> {
        records += 1
        return recordResult
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
