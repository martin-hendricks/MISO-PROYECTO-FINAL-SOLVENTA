package com.grupo8_uniandes.solventa.home

import androidx.compose.ui.test.SemanticsMatcher
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.getBoundsInRoot
import androidx.compose.ui.test.hasTestTag
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyle
import com.grupo8_uniandes.solventa.ui.components.SolventaButtonStyleKey
import com.grupo8_uniandes.solventa.ui.shell.InicioScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class InicioScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenNoSlots_whenInicioShows_thenOnlyNuevaCotizacion() {
        show(HomePanel())
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
        rule.onNodeWithText("COTIZAR OTRO SEGURO").assertIsDisplayed()
        rule.onNodeWithText("Nueva cotización").assertIsDisplayed()
        rule.onNode(filled("action_new_quote")).assertIsDisplayed()
        rule.onAllNodesWithText("COTIZACIÓN POR ACEPTAR").assertCountEquals(0)
        rule.onAllNodesWithText("TUS PÓLIZAS").assertCountEquals(0)
        rule.onAllNodesWithText("TUS SINIESTROS").assertCountEquals(0)
        rule.onAllNodesWithText("VIDA HIPOTECARIO").assertCountEquals(0)
        rule.onAllNodesWithTag("home_offer").assertCountEquals(0)
        rule.onAllNodesWithTag("home_policy").assertCountEquals(0)
        rule.onAllNodesWithTag("home_claim").assertCountEquals(0)
        rule.onAllNodesWithTag("action_accept_offer").assertCountEquals(0)
        rule.onAllNodesWithTag("home_vida_crediticia").assertCountEquals(0)
        rule.onAllNodesWithText("SOL-0001").assertCountEquals(0)
        rule.onAllNodes(hasTestTag("partner_results")).assertCountEquals(0)
    }

    @Test
    fun givenThreeSlots_whenInicioShows_thenIdsUseTheCards() {
        show(HomePanel(offerId = "Q-1", policyId = "POL-1", claimId = "CLM-1"))
        rule.onNodeWithText("COTIZACIÓN POR ACEPTAR").assertIsDisplayed()
        rule.onNodeWithTag("home_offer").assertIsDisplayed()
        rule.onNodeWithText("Q-1").assertIsDisplayed()
        rule.onNodeWithText("TUS PÓLIZAS").assertIsDisplayed()
        rule.onNodeWithTag("home_policy").assertIsDisplayed()
        rule.onNodeWithText("Detalle de póliza").assertIsDisplayed()
        rule.onNodeWithText("POL-1").assertIsDisplayed()
        rule.onNodeWithText("TUS SINIESTROS").assertIsDisplayed()
        rule.onNodeWithTag("home_claim").assertIsDisplayed()
        rule.onNodeWithText("CLM-1").assertIsDisplayed()
        rule.onNodeWithText("COTIZAR OTRO SEGURO").assertIsDisplayed()
        val policyTop = rule.onNodeWithTag("home_policy").getBoundsInRoot().top
        val claimTop = rule.onNodeWithTag("home_claim").getBoundsInRoot().top
        val quoteTop = rule.onNodeWithTag("action_new_quote").getBoundsInRoot().top
        assertTrue(policyTop < quoteTop)
        assertTrue(claimTop < quoteTop)
        rule.onAllNodesWithText("Avisos de siniestro").assertCountEquals(0)
        rule.onAllNodes(hasTestTag("partner_results")).assertCountEquals(0)
        rule.onAllNodesWithText("SOL-0001").assertCountEquals(0)
    }

    @Test
    fun givenOffer_whenInicioShows_thenAcceptIsFilledAboveTonalQuote() {
        var accepted: String? = null
        show(HomePanel(offerId = "Q-9"), onAcceptOffer = { accepted = it })
        rule.onNodeWithText("COTIZACIÓN POR ACEPTAR").assertIsDisplayed()
        rule.onNode(filled("action_accept_offer")).assertIsDisplayed()
        rule.onNode(outlined("action_new_quote")).assertIsDisplayed()
        val acceptTop = rule.onNodeWithTag("action_accept_offer").getBoundsInRoot().top
        val quoteTop = rule.onNodeWithTag("action_new_quote").getBoundsInRoot().top
        assertTrue(acceptTop < quoteTop)
        rule.onNodeWithTag("action_accept_offer").performClick()
        assertEquals("Q-9", accepted)
    }

    @Test
    fun givenNoOffer_whenInicioShows_thenQuoteIsFilledAndAcceptIsAbsent() {
        show(HomePanel())
        rule.onAllNodesWithTag("action_accept_offer").assertCountEquals(0)
        rule.onAllNodesWithText("COTIZACIÓN POR ACEPTAR").assertCountEquals(0)
        rule.onNodeWithText("COTIZAR OTRO SEGURO").assertIsDisplayed()
        rule.onNode(filled("action_new_quote")).assertIsDisplayed()
    }

    @Test
    fun givenOrigination_whenVidaTapped_thenNoOtherCallbackRuns() {
        var quoted = 0
        var accepted: String? = null
        var policy: String? = null
        var claim: String? = null
        var mortgage = 0
        show(
            HomePanel(
                offerId = "Q-1",
                policyId = "POL-1",
                claimId = "CLM-1",
                vidaCrediticia = true,
            ),
            onNewQuote = { quoted += 1 },
            onAcceptOffer = { accepted = it },
            onOpenPolicy = { policy = it },
            onOpenClaim = { claim = it },
            onOpenMortgage = { mortgage += 1 },
        )
        rule.onNodeWithText("VIDA HIPOTECARIO").assertIsDisplayed()
        rule.onNodeWithTag("home_vida_crediticia").assertIsDisplayed()
        rule.onNodeWithText("Vida Crediticia").assertIsDisplayed()
        rule.onNodeWithTag("home_vida_crediticia").performClick()
        assertEquals(0, quoted)
        assertNull(accepted)
        assertNull(policy)
        assertNull(claim)
        assertEquals(1, mortgage)
    }

    @Test
    fun givenDefaults_whenSlotsAreTapped_thenEmptyCallbacksDoNotThrow() {
        rule.setContent {
            SolventaTheme {
                InicioScreen(
                    state = HomeUiState(
                        panel = HomePanel(offerId = "Q-1", policyId = "POL-1", claimId = "CLM-1"),
                    ),
                    onNewQuote = {},
                )
            }
        }
        rule.onNodeWithTag("action_accept_offer").performClick()
        rule.onNodeWithTag("home_policy").performClick()
        rule.onNodeWithTag("home_claim").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
    }

    @Test
    fun givenAFailedRefresh_whenInicioShows_thenTheLineAppearsAndTheCardsStay() {
        show(HomePanel(offerId = "Q-kept", policyId = "POL-kept"), failed = true)
        rule.onNodeWithTag("load_failed").assertIsDisplayed()
        rule.onNodeWithText("No se pudo cargar la información.").assertIsDisplayed()
        rule.onNodeWithTag("home_offer").assertIsDisplayed()
        rule.onNodeWithTag("home_policy").assertIsDisplayed()
    }

    @Test
    fun givenOrigination_whenVidaUsesTheDefaultCallback_thenInicioStays() {
        rule.setContent {
            SolventaTheme {
                InicioScreen(
                    state = HomeUiState(panel = HomePanel(vidaCrediticia = true)),
                    onNewQuote = {},
                )
            }
        }
        rule.onNodeWithTag("home_vida_crediticia").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
    }

    @Test
    fun givenNoOrigination_whenInicioShows_thenVidaIsAbsent() {
        show(HomePanel(vidaCrediticia = false))
        rule.onAllNodesWithTag("home_vida_crediticia").assertCountEquals(0)
        rule.onAllNodesWithText("Vida Crediticia").assertCountEquals(0)
        rule.onAllNodesWithText("VIDA HIPOTECARIO").assertCountEquals(0)
    }

    private fun show(
        panel: HomePanel,
        failed: Boolean = false,
        onNewQuote: () -> Unit = {},
        onAcceptOffer: (String) -> Unit = {},
        onOpenPolicy: (String) -> Unit = {},
        onOpenClaim: (String) -> Unit = {},
        onOpenMortgage: () -> Unit = {},
    ) {
        rule.setContent {
            SolventaTheme {
                InicioScreen(
                    state = HomeUiState(panel = panel, failed = failed),
                    onNewQuote = onNewQuote,
                    onAcceptOffer = onAcceptOffer,
                    onOpenPolicy = onOpenPolicy,
                    onOpenClaim = onOpenClaim,
                    onOpenMortgage = onOpenMortgage,
                )
            }
        }
    }

    private fun filled(tag: String) =
        hasTestTag(tag) and SemanticsMatcher.expectValue(SolventaButtonStyleKey, SolventaButtonStyle.Filled)

    private fun outlined(tag: String) =
        hasTestTag(tag) and SemanticsMatcher.expectValue(SolventaButtonStyleKey, SolventaButtonStyle.Outlined)
}
