package com.grupo8_uniandes.solventa.consent

import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.domain.consent.ConsentRecord
import com.grupo8_uniandes.solventa.domain.consent.ConsentRepository
import com.grupo8_uniandes.solventa.domain.consent.ConsentSnapshot
import com.grupo8_uniandes.solventa.domain.consent.ConsentState
import com.grupo8_uniandes.solventa.ui.consent.ConsentEffect
import com.grupo8_uniandes.solventa.ui.consent.ConsentSurface
import com.grupo8_uniandes.solventa.ui.consent.ConsentUiState
import com.grupo8_uniandes.solventa.ui.consent.ConsentViewModel
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class ConsentViewModelTest {
    private val change = RecordingChange()

    @Test
    fun givenAlta_whenOpened_thenSwitchIsOffAndConfirmIsDisabled() {
        val viewModel = alta()

        assertFalse(viewModel.state.value.switchOn)
        assertFalse(viewModel.state.value.confirmEnabled)
        assertNull(viewModel.state.value.effect)
        assertEquals(0, change.grants)
    }

    @Test
    fun givenAltaSwitchOn_whenConfirm_thenHomeOnce() {
        val viewModel = alta()
        viewModel.onSwitch(true)

        assertTrue(viewModel.state.value.confirmEnabled)
        viewModel.confirm()
        viewModel.confirm()

        assertEquals(ConsentEffect.OpenHome, viewModel.state.value.effect)
        assertEquals(1, change.grants)
        assertEquals(0, change.revokes)
    }

    @Test
    fun givenAltaSwitchOn_whenBack_thenAccountWithoutGrant() {
        val viewModel = alta()
        viewModel.onSwitch(true)

        viewModel.back()

        assertEquals(ConsentEffect.OpenAccount, viewModel.state.value.effect)
        assertEquals(0, change.grants)
        assertEquals(0, change.revokes)
    }

    @Test
    fun givenGrantedSheet_whenCloseAfterMove_thenUseCaseIsNotCalled() {
        val viewModel = profile(ConsentState.Granted)
        assertTrue(viewModel.state.value.switchOn)
        assertFalse(viewModel.state.value.confirmEnabled)
        viewModel.onSwitch(false)

        viewModel.close()

        assertTrue(viewModel.state.value.switchOn)
        assertEquals(ConsentState.Granted, viewModel.state.value.stored)
        assertNull(viewModel.state.value.effect)
        assertEquals(0, change.grants)
        assertEquals(0, change.revokes)
    }

    @Test
    fun givenGrantedSheet_whenSwitchOffAndConfirm_thenHubRevokedAndStillSignedIn() {
        val viewModel = profile(ConsentState.Granted)
        viewModel.onSwitch(false)

        viewModel.confirm()

        assertEquals(ConsentEffect.ReturnToHub, viewModel.state.value.effect)
        assertEquals(ConsentState.Revoked, viewModel.state.value.stored)
        assertEquals(1, change.revokes)
        assertEquals(0, change.grants)
    }

    @Test
    fun givenRevokedSheet_whenSwitchOnAndConfirm_thenHubGrantedWithoutAlta() {
        val viewModel = profile(ConsentState.Revoked)
        assertFalse(viewModel.state.value.switchOn)
        viewModel.onSwitch(true)

        viewModel.confirm()

        assertEquals(ConsentEffect.ReturnToHub, viewModel.state.value.effect)
        assertEquals(ConsentState.Granted, viewModel.state.value.stored)
        assertEquals(1, change.grants)
    }

    @Test
    fun givenAltaSwitchOff_whenConfirmOrSwitchAfterHandoff_thenUseCaseStaysIdle() {
        val viewModel = alta()

        viewModel.confirm()

        assertNull(viewModel.state.value.effect)
        assertEquals(0, change.grants)
        viewModel.onSwitch(true)
        viewModel.confirm()
        viewModel.onSwitch(false)
        viewModel.back()

        assertEquals(ConsentEffect.OpenHome, viewModel.state.value.effect)
        assertTrue(viewModel.state.value.switchOn)
        assertEquals(1, change.grants)
    }

    @Test
    fun givenProfileSwitchMatchesStored_whenConfirm_thenUseCaseIsNotCalled() {
        val viewModel = profile(ConsentState.Revoked)

        viewModel.confirm()

        assertNull(viewModel.state.value.effect)
        assertEquals(0, change.grants)
        assertEquals(0, change.revokes)
        assertEquals(
            ConsentUiState(
                stored = ConsentState.Revoked,
                switchOn = false,
                confirmEnabled = false,
                effect = null,
            ),
            viewModel.state.value,
        )
    }

    private fun alta() = ConsentViewModel(
        change = change,
        initial = ConsentSnapshot(ConsentState.NotGranted),
        surface = ConsentSurface.Alta,
    )

    private fun profile(stored: ConsentState) = ConsentViewModel(
        change = change,
        initial = ConsentSnapshot(stored),
        surface = ConsentSurface.Profile,
    )
}

private class RecordingChange : ChangeDataTreatment(
    object : ConsentRepository {
        override fun read(): ConsentSnapshot = ConsentSnapshot()

        override fun append(record: ConsentRecord) = Unit
    },
    now = { 0L },
) {
    var grants = 0
    var revokes = 0

    override fun grant(): ConsentSnapshot {
        grants += 1
        return ConsentSnapshot(ConsentState.Granted)
    }

    override fun revoke(): ConsentSnapshot {
        revokes += 1
        return ConsentSnapshot(ConsentState.Revoked)
    }
}
