package com.grupo8_uniandes.solventa.home

import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performTextInput
import androidx.compose.ui.unit.dp
import androidx.navigation.compose.rememberNavController
import com.grupo8_uniandes.solventa.domain.home.HomePanel
import com.grupo8_uniandes.solventa.navigation.CustomerNavHost
import com.grupo8_uniandes.solventa.ui.shell.EmisionEnCursoScreen
import com.grupo8_uniandes.solventa.ui.shell.SignedInShell
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class InicioNavigationTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenOffer_whenAccepted_thenIssuanceShowsThatId() {
        show(HomePanel(offerId = "Q-42"))
        rule.onNodeWithTag("action_accept_offer").performClick()
        rule.onNodeWithTag("screen_emision").assertIsDisplayed()
        rule.onNodeWithTag("emision_body").assertIsDisplayed()
        rule.onAllNodesWithText("Q-42").assertCountEquals(0)
        rule.onAllNodesWithTag("screen_cotizacion").assertCountEquals(0)
    }

    @Test
    fun givenInicio_whenNuevaCotizacion_thenQuoteOpensWithoutIssuance() {
        show(HomePanel(offerId = "Q-42"))
        rule.onNodeWithTag("action_new_quote").performClick()
        rule.onNodeWithTag("screen_cotizacion").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_emision").assertCountEquals(0)
    }

    @Test
    fun givenNoOfferIdArgument_whenIssuing_thenTheIdStaysHidden() {
        rule.setContent {
            SolventaTheme {
                EmisionEnCursoScreen(onFinished = {})
            }
        }
        rule.onNodeWithTag("screen_emision").assertIsDisplayed()
        rule.onNodeWithTag("emision_body").assertIsDisplayed()
    }

    @Test
    fun givenOfferCard_whenOpened_thenVerOfertaShowsThePreparedPremium() {
        show(HomePanel(offerId = "COT-1042"))
        rule.onNodeWithTag("home_offer").performClick()
        rule.onNodeWithTag("screen_ver_oferta").assertIsDisplayed()
        rule.onNodeWithText("Prima $89.000 COP").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_emision").assertCountEquals(0)
    }

    @Test
    fun givenTheThreeAnswers_whenCotizar_thenVerOfertaOpensOnThePreparedPremium() {
        show(HomePanel())
        rule.onNodeWithTag("action_new_quote").performClick()
        rule.onNodeWithTag("field_device_value").performTextInput("2400000")
        rule.onNodeWithTag("field_brand_model").performTextInput("Pixel")
        rule.onNodeWithTag("answer_no").performClick()
        rule.onNodeWithTag("action_quote").performClick()
        rule.onNodeWithTag("screen_ver_oferta").assertIsDisplayed()
        rule.onNodeWithText("Prima $89.000 COP").assertIsDisplayed()
    }

    @Test
    fun givenIncompleteQuote_whenCotizar_thenItStaysOffIssuance() {
        show(HomePanel())
        rule.onNodeWithTag("action_new_quote").performClick()
        rule.onNodeWithTag("action_quote").performClick()
        rule.onNodeWithTag("screen_cotizacion").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_emision").assertCountEquals(0)
    }

    @Test
    fun givenPolicy_whenOpened_thenDetailShowsThatIdAndBackReturnsToTheList() {
        show(HomePanel(policyId = "POL-9"))
        rule.onNodeWithTag("home_policy").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithTag("policy_numero").assertTextEquals("POL-88219-CO")
        rule.onNodeWithText("Cancelar").performClick()
        rule.onNodeWithTag("screen_polizas").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
    }

    @Test
    fun givenInicio_whenReportarSiniestro_thenSiniestrosOpensAndTheActionLeaves() {
        rule.setContent {
            SolventaTheme {
                SignedInShell(homeState = HomeUiState())
            }
        }
        rule.onNodeWithText("Reportar siniestro").assertIsDisplayed()
        rule.onNodeWithTag("solventa_floating_action").performClick()
        rule.onNodeWithTag("screen_siniestros").assertIsDisplayed()
        rule.onAllNodesWithTag("solventa_floating_action").assertCountEquals(0)
    }

    @Test
    fun givenClaim_whenOpened_thenDetailShowsThatIdAndVolverReturnsToTheList() {
        show(HomePanel(claimId = "CLM-9"))
        rule.onNodeWithTag("home_claim").performClick()
        rule.onNodeWithTag("screen_siniestro_detalle").assertIsDisplayed()
        rule.onNodeWithText("CLM-9").assertIsDisplayed()
        rule.onNodeWithTag("action_siniestro_volver").performClick()
        rule.onNodeWithTag("screen_siniestros").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_inicio").assertCountEquals(0)
    }

    private fun show(panel: HomePanel) {
        rule.setContent {
            SolventaTheme {
                CustomerNavHost(
                    navController = rememberNavController(),
                    homeState = HomeUiState(panel = panel),
                    contentPadding = PaddingValues(0.dp),
                )
            }
        }
    }
}
