package com.grupo8_uniandes.solventa.mortgage

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.bff.StandInAnswer
import com.grupo8_uniandes.solventa.domain.bff.mortgage.CreditProfile
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageQuote
import com.grupo8_uniandes.solventa.domain.bff.mortgage.MortgageRepository
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.ui.shell.VidaHipotecarioFlow
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class MortgageOfferFlowTest {
    @get:Rule
    val rule = createComposeRule()

    private class FakeMortgage(
        var answer: StandInAnswer<MortgageQuote> = StandInAnswer.Ready(QUOTE),
        val gate: CompletableDeferred<Unit>? = null,
    ) : MortgageRepository {
        val requests = mutableListOf<CreditProfile>()

        override suspend fun offer(profile: CreditProfile): StandInAnswer<MortgageQuote> {
            requests += profile
            gate?.await()
            return answer
        }
    }

    @Before
    fun setMain() {
        Dispatchers.setMain(UnconfinedTestDispatcher())
    }

    @After
    fun resetMain() {
        Dispatchers.resetMain()
    }

    private fun render(
        repository: MortgageRepository,
        onAccept: (Long, String) -> Unit = { _, _ -> },
        onDecline: () -> Unit = {},
    ): MortgageOfferViewModel {
        val viewModel = MortgageOfferViewModel(repository)
        rule.setContent {
            SolventaTheme {
                VidaHipotecarioFlow(
                    viewModel = viewModel,
                    region = Region.Colombia,
                    onAccept = onAccept,
                    onDecline = onDecline,
                )
            }
        }
        return viewModel
    }

    @Test
    fun givenTheCard_whenTheFlowOpens_thenItAsksForTheProfilingConsentFirst() {
        val repository = FakeMortgage()
        render(repository)

        rule.onNodeWithTag("screen_consentimiento_hipotecario").assertIsDisplayed()
        rule.onNodeWithText("Open Finance", substring = true).assertIsDisplayed()
        rule.onNodeWithText("Open Data", substring = true).assertIsDisplayed()
        rule.onAllNodesWithTag("screen_oferta_hipotecario").assertCountEquals(0)
        assertTrue(repository.requests.isEmpty())
    }

    @Test
    fun givenTheConsentStep_whenDeclined_thenNoProfileIsRequestedAndTheCustomerLeaves() {
        val repository = FakeMortgage()
        var declined = 0
        render(repository, onDecline = { declined += 1 })

        rule.onNodeWithTag("action_decline_profiling").performClick()

        assertEquals(1, declined)
        assertTrue(repository.requests.isEmpty())
    }

    @Test
    fun givenTheConsentStep_whenAuthorized_thenTheRealOfferIsShownWithItsFactors() {
        val repository = FakeMortgage()
        val accepted = mutableListOf<Pair<Long, String>>()
        render(repository, onAccept = { prima, moneda -> accepted += prima to moneda })

        rule.onNodeWithTag("action_authorize_profiling").performClick()
        rule.waitForIdle()

        assertEquals(1, repository.requests.size)
        assertTrue(repository.requests.single().consentimientoPerfil)
        rule.onNodeWithTag("screen_oferta_hipotecario").assertIsDisplayed()
        rule.onNodeWithText("$64.000 COP / mes").assertIsDisplayed()
        rule.onNodeWithText("Nivel de ingresos estimado", substring = true).assertIsDisplayed()
        rule.onNodeWithText("Zona de riesgo", substring = true).assertIsDisplayed()
        rule.onAllNodesWithTag("mortgage_offer_degraded").assertCountEquals(0)
        rule.onNodeWithTag("action_accept_mortgage").performClick()
        assertEquals(listOf(64_000L to "COP"), accepted)
    }

    @Test
    fun givenADegradedProfile_whenTheOfferShows_thenTheCustomerIsWarned() {
        render(FakeMortgage(answer = StandInAnswer.Ready(QUOTE.copy(degradada = true))))

        rule.onNodeWithTag("action_authorize_profiling").performClick()
        rule.waitForIdle()

        rule.onNodeWithTag("mortgage_offer_degraded").assertIsDisplayed()
    }

    @Test
    fun givenTheBffFails_whenAuthorized_thenTheCustomerCanRetry() {
        val repository = FakeMortgage(answer = StandInAnswer.Failed)
        render(repository)

        rule.onNodeWithTag("action_authorize_profiling").performClick()
        rule.waitForIdle()
        rule.onNodeWithTag("mortgage_offer_unavailable").assertIsDisplayed()

        repository.answer = StandInAnswer.Ready(QUOTE)
        rule.onNodeWithTag("action_retry_mortgage").performClick()
        rule.waitForIdle()

        assertEquals(2, repository.requests.size)
        rule.onNodeWithText("$64.000 COP / mes").assertIsDisplayed()
    }

    @Test
    fun givenAnOfferInFlight_whenAuthorizedAgain_thenTheBffIsCalledOnce() {
        val gate = CompletableDeferred<Unit>()
        val repository = FakeMortgage(gate = gate)
        val viewModel = MortgageOfferViewModel(repository)

        viewModel.authorize()
        viewModel.authorize()
        assertEquals(MortgageOfferUi.Requesting, viewModel.state.value)
        gate.complete(Unit)

        assertEquals(1, repository.requests.size)
        assertEquals(MortgageOfferUi.Offer(QUOTE), viewModel.state.value)
    }

    private companion object {
        val QUOTE = MortgageQuote(
            ramo = "Vida hipotecario",
            estado = "oferta_vigente",
            prima = 64_000L,
            moneda = "COP",
            factores = listOf("nivel_ingresos_estimado", "zona_riesgo"),
            degradada = false,
        )
    }
}
