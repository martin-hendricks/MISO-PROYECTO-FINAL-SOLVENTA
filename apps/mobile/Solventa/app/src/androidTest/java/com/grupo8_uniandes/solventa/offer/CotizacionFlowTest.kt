package com.grupo8_uniandes.solventa.offer

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.getBoundsInRoot
import androidx.compose.ui.test.junit4.ComposeTestRule
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import androidx.compose.ui.test.performTextInput
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.home.HomeUiState
import com.grupo8_uniandes.solventa.ui.shell.SignedInShell
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertTrue
import org.junit.Rule
import org.junit.Test

class CotizacionFlowTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenTheOfferCard_whenOpened_thenVerOfertaShowsThePreparedPremiumAndInicioStaysSelected() {
        show(offerPanel())
        rule.onNodeWithTag("home_offer").performScrollTo().performClick()
        rule.waitForTag("screen_ver_oferta")
        rule.onNodeWithText("Prima $89.000 COP").assertIsDisplayed()
        rule.onNodeWithTag("tab_Inicio").assertIsSelected()
        rule.onNodeWithTag("bottom_bar").assertIsDisplayed()
    }

    @Test
    fun givenACurrentOffer_whenAcceptedFromInicio_thenIssuanceShowsThatId() {
        show(offerPanel())
        val acceptTop = rule.onNodeWithTag("action_accept_offer").getBoundsInRoot().top
        val quoteTop = rule.onNodeWithTag("action_new_quote").getBoundsInRoot().top
        assertTrue(acceptTop < quoteTop)
        rule.onNodeWithTag("action_accept_offer").performScrollTo().performClick()
        rule.waitForTag("screen_emision")
        rule.onNodeWithTag("emision_body").assertIsDisplayed()
        rule.onAllNodesWithText("COT-1042").assertCountEquals(0)
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
    }

    @Test
    fun givenTheThreeAnswers_whenCotizar_thenVerOfertaShowsTheSamePremium() {
        show(offerPanel())
        rule.onNodeWithTag("action_new_quote").performScrollTo().performClick()
        rule.waitForTag("screen_cotizacion")
        rule.onNodeWithTag("field_device_value").performScrollTo().performTextInput("2400000")
        rule.onNodeWithTag("field_brand_model").performScrollTo().performTextInput("Pixel")
        rule.onNodeWithTag("answer_no").performScrollTo().performClick()
        rule.onNodeWithTag("action_quote").performScrollTo().performClick()
        rule.waitForTag("screen_ver_oferta")
        rule.onNodeWithText("Prima $89.000 COP").assertIsDisplayed()
    }

    @Test
    fun givenNuevaCotizacion_whenCancel_thenInicioReturnsWithoutIssuance() {
        show(offerPanel())
        rule.onNodeWithTag("action_new_quote").performScrollTo().performClick()
        rule.waitForTag("screen_cotizacion")
        rule.onNodeWithTag("action_cancel_quote").performScrollTo().performClick()
        rule.waitForTag("screen_inicio")
        rule.onAllNodesWithTag("screen_emision").assertCountEquals(0)
    }

    private fun offerPanel() = HomeUiState(panel = HomePanel(offerId = "COT-1042"))

    private fun show(state: HomeUiState) {
        rule.setContent {
            SolventaTheme {
                SignedInShell(homeState = state)
            }
        }
    }
}

private fun ComposeTestRule.waitForTag(tag: String) {
    waitUntil(timeoutMillis = 30_000) {
        onAllNodesWithTag(tag).fetchSemanticsNodes().isNotEmpty()
    }
}
