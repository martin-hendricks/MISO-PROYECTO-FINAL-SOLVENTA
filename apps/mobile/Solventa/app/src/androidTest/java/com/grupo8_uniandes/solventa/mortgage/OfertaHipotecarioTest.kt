package com.grupo8_uniandes.solventa.mortgage

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertHasNoClickAction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.issuance.confirmReviewCard
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.ui.shell.SignedInShell
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class OfertaHipotecarioTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Before
    fun accessibilityChecks() {
        rule.enableAccessibilityChecks()
    }

    @Test
    fun givenTheReviewOffer_whenOpened_thenPremiumAndCoverageAreVisible() {
        openOffer()
        rule.onNodeWithText("Vida hipotecario · paso 2 de 3").assertIsDisplayed()
        rule.onNodeWithText("Vida hipotecario · oferta en firme").assertIsDisplayed()
        rule.onNodeWithText("Protección de pagos · prima según tu perfil").assertIsDisplayed()
        rule.onNodeWithText("$64.000 COP / mes").assertIsDisplayed()
    }

    @Test
    fun givenTheReviewOffer_whenOpened_thenTheFactorsExplainItWithoutDegradation() {
        openOffer()
        rule.onNodeWithTag("mortgage_offer_factors").assertIsDisplayed()
        rule.onAllNodesWithText("Consentimiento Vida Crediticia").assertCountEquals(0)
        rule.onAllNodesWithTag("mortgage_offer_degraded").assertCountEquals(0)
    }

    @Test
    fun givenTheCard_whenTheProfilingConsentIsDeclined_thenInicioStays() {
        openConsent()
        rule.onNodeWithTag("action_decline_profiling").performClick()
        rule.waitForTag("screen_inicio")
        rule.onAllNodesWithTag("screen_oferta_hipotecario").assertCountEquals(0)
    }

    @Test
    fun givenTheReviewOffer_whenAccepted_thenExistingIssuanceOpens() {
        openOffer()
        rule.onNodeWithTag("action_accept_mortgage").performClick()
        rule.confirmReviewCard()
        rule.waitForIssuance()
        rule.onAllNodesWithText("Consentimiento Vida Crediticia").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_oferta_hipotecario").assertCountEquals(0)
    }

    @Test
    fun givenTheReviewOffer_whenReviewLater_thenInicioKeepsTheOffer() {
        openOffer()
        rule.onNodeWithTag("action_review_later").performClick()
        rule.waitForTag("screen_inicio")
        rule.onAllNodesWithTag("screen_emision").assertCountEquals(0)
        rule.onNodeWithTag("home_vida_crediticia").performScrollTo().performClick()
        rule.waitForTag("screen_consentimiento_hipotecario")
    }

    @Test
    fun givenTheReviewOffer_whenBack_thenInicioKeepsTheOffer() {
        openOffer()
        rule.onNodeWithTag("action_volver").performClick()
        rule.waitForTag("screen_inicio")
        rule.onAllNodesWithTag("screen_emision").assertCountEquals(0)
        rule.onNodeWithTag("home_vida_crediticia").performScrollTo().performClick()
        rule.waitForTag("screen_consentimiento_hipotecario")
    }

    @Test
    fun givenTheReviewOffer_whenMarksAreUsed_thenTheScreenStays() {
        openOffer()
        rule.onNodeWithTag("mortgage_offer_chevron", useUnmergedTree = true).assertHasNoClickAction()
        rule.onNodeWithTag("mortgage_identity_mark", useUnmergedTree = true).assertHasNoClickAction()
        rule.onNodeWithTag("screen_oferta_hipotecario").assertIsDisplayed()
    }

    @Test
    fun givenTheReviewOffer_whenShown_thenInicioIsSelectedAndNoPrompt() {
        openOffer()
        rule.onNodeWithTag("tab_Inicio").assertIsSelected()
        rule.onNodeWithTag("tab_Polizas").assertIsDisplayed()
        rule.onNodeWithTag("tab_Siniestros").assertIsDisplayed()
        rule.onNodeWithTag("tab_Perfil").assertIsDisplayed()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)
        rule.onAllNodesWithText("Permitir").assertCountEquals(0)
        rule.onNodeWithTag("mortgage_identity_mark", useUnmergedTree = true).assertHasNoClickAction()
        rule.onNodeWithTag("screen_oferta_hipotecario").assertIsDisplayed()
    }

    private fun openConsent() {
        rule.setContent {
            SolventaTheme {
                SignedInShell(homeState = HomeUiState(panel = HomePanel(vidaCrediticia = true)))
            }
        }
        rule.onNodeWithTag("home_vida_crediticia").performScrollTo().performClick()
        rule.waitForTag("screen_consentimiento_hipotecario")
    }

    private fun openOffer() {
        openConsent()
        rule.onNodeWithTag("action_authorize_profiling").performClick()
        rule.waitForTag("screen_oferta_hipotecario")
    }
}

private fun ComposeTestRule.waitForTag(tag: String) {
    waitUntil(timeoutMillis = 30_000) {
        onAllNodesWithTag(tag).fetchSemanticsNodes().isNotEmpty()
    }
}

private fun ComposeTestRule.waitForIssuance() {
    waitUntil(timeoutMillis = 30_000) {
        listOf("screen_emision", "screen_issued", "screen_rejection").any { tag ->
            onAllNodesWithTag(tag).fetchSemanticsNodes().isNotEmpty()
        }
    }
}
