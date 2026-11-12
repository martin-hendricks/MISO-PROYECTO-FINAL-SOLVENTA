package com.grupo8_uniandes.solventa.shell

import android.content.Context
import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.data.consent.ConsentPrefsFile
import com.grupo8_uniandes.solventa.data.consent.SharedPrefsConsentRepository
import com.grupo8_uniandes.solventa.data.region.RegionPrefsFile
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ProfilingConsent
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ProfilingConsentRepository
import com.grupo8_uniandes.solventa.domain.consent.ChangeDataTreatment
import com.grupo8_uniandes.solventa.ui.shell.PerfilScreen
import com.grupo8_uniandes.solventa.ui.shell.ProfilingConsentViewModel
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class ProfilingConsentProfileTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    private val context = ApplicationProvider.getApplicationContext<Context>()

    private class FakeProfilingConsent(
        var current: StandInAnswer<ProfilingConsent> = StandInAnswer.Ready(GRANTED),
        var revocation: StandInAnswer<ProfilingConsent> = StandInAnswer.Ready(REVOKED),
        val gate: CompletableDeferred<Unit>? = null,
    ) : ProfilingConsentRepository {
        var revocations = 0

        override suspend fun read(): StandInAnswer<ProfilingConsent> = current

        override suspend fun revoke(): StandInAnswer<ProfilingConsent> {
            revocations += 1
            gate?.await()
            return revocation
        }
    }

    @Before
    fun setUp() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
        context.getSharedPreferences(RegionPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
        context.getSharedPreferences(ConsentPrefsFile, Context.MODE_PRIVATE).edit().clear().commit()
    }

    @After
    fun tearDown() {
        Dispatchers.resetMain()
    }

    private fun render(repository: ProfilingConsentRepository) {
        rule.setContent {
            SolventaTheme {
                PerfilScreen(profilingConsent = repository)
            }
        }
    }

    @Test
    fun givenAConsentInForce_whenTheHubOpens_thenTheRowShowsWhenItWasGranted() {
        render(FakeProfilingConsent())

        rule.onNodeWithTag("profile_profiling_consent").assertIsDisplayed()
        rule.onNodeWithText("Perfilamiento para vida hipotecario").assertIsDisplayed()
        rule.onNodeWithText("Otorgado el 01/10/2026").assertIsDisplayed()
        rule.onAllNodesWithTag("sheet_profiling_consent").assertCountEquals(0)
    }

    @Test
    fun givenNoConsentOrAFailedRead_whenTheHubOpens_thenThereIsNoRow() {
        render(FakeProfilingConsent(current = StandInAnswer.Ready(ProfilingConsent.None)))
        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
        rule.onAllNodesWithTag("profile_profiling_consent").assertCountEquals(0)
    }

    @Test
    fun givenAFailedRead_whenTheHubOpens_thenThereIsNoRow() {
        render(FakeProfilingConsent(current = StandInAnswer.Failed))
        rule.onNodeWithTag("screen_perfil").assertIsDisplayed()
        rule.onAllNodesWithTag("profile_profiling_consent").assertCountEquals(0)
    }

    @Test
    fun givenTheSheet_whenCancelled_thenNothingIsRevoked() {
        val repository = FakeProfilingConsent()
        render(repository)

        rule.onNodeWithTag("profile_profiling_consent").performClick()
        rule.onNodeWithTag("sheet_profiling_consent").assertIsDisplayed()
        rule.onNodeWithText("Open Finance y Open Data", substring = true).assertIsDisplayed()
        rule.onNodeWithTag("action_profiling_consent_cancel").performClick()

        rule.onAllNodesWithTag("sheet_profiling_consent").assertCountEquals(0)
        rule.onNodeWithText("Otorgado el 01/10/2026").assertIsDisplayed()
        assertEquals(0, repository.revocations)
    }

    @Test
    fun givenTheSheet_whenRevoked_thenTheRowShowsTheRevocationAndCannotRevokeAgain() {
        val repository = FakeProfilingConsent()
        render(repository)

        rule.onNodeWithTag("profile_profiling_consent").performClick()
        rule.onNodeWithTag("action_revoke_profiling_consent").performClick()
        rule.waitForIdle()

        assertEquals(1, repository.revocations)
        rule.onAllNodesWithTag("sheet_profiling_consent").assertCountEquals(0)
        rule.onNodeWithText("Revocado el 11/11/2026").assertIsDisplayed()
        rule.onNodeWithTag("profile_profiling_consent").performClick()
        rule.onAllNodesWithTag("sheet_profiling_consent").assertCountEquals(0)
    }

    @Test
    fun givenTheBffFails_whenRevoked_thenTheConsentStaysAndTheCustomerIsTold() {
        val repository = FakeProfilingConsent(revocation = StandInAnswer.Failed)
        render(repository)

        rule.onNodeWithTag("profile_profiling_consent").performClick()
        rule.onNodeWithTag("action_revoke_profiling_consent").performClick()
        rule.waitForIdle()

        rule.onNodeWithTag("profile_profiling_consent_error").assertIsDisplayed()
        rule.onNodeWithText("Otorgado el 01/10/2026").assertIsDisplayed()
    }

    @Test
    fun givenADataConsent_whenTheProfilingConsentIsRevoked_thenTheDataConsentStays() {
        ChangeDataTreatment(SharedPrefsConsentRepository(context)) { 1L }.grant()
        render(FakeProfilingConsent())

        rule.onNodeWithTag("profile_profiling_consent").performClick()
        rule.onNodeWithTag("action_revoke_profiling_consent").performClick()
        rule.waitForIdle()

        rule.onNodeWithTag("profile_consent").assertIsDisplayed()
        rule.onNodeWithText("otorgado").assertIsDisplayed()
    }

    @Test
    fun givenARevocationInFlight_whenRevokedAgain_thenTheBffIsCalledOnce() {
        val gate = CompletableDeferred<Unit>()
        val repository = FakeProfilingConsent(gate = gate)
        val viewModel = ProfilingConsentViewModel(repository)

        viewModel.open()
        viewModel.revoke()
        viewModel.revoke()
        gate.complete(Unit)

        assertEquals(1, repository.revocations)
        assertEquals(REVOKED, viewModel.state.value.consent)
    }

    private companion object {
        val GRANTED = ProfilingConsent.Granted("2026-10-01T10:00:00Z")
        val REVOKED = ProfilingConsent.Revoked("2026-11-11T15:30:00Z")
    }
}
