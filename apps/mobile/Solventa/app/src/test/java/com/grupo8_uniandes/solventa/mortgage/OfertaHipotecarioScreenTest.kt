package com.grupo8_uniandes.solventa.mortgage

import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertHasNoClickAction
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.bff.mortgage.ShowMortgageOffer
import com.grupo8_uniandes.solventa.ui.shell.OfertaHipotecarioScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class OfertaHipotecarioScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenTheReviewOffer_whenShown_thenTheCardAndTheTwoActions() {
        val offer = ShowMortgageOffer().show()
        var accepted = 0
        var later = 0
        rule.setContent {
            SolventaTheme {
                OfertaHipotecarioScreen(
                    offer = offer,
                    onAccept = { accepted += 1 },
                    onReviewLater = { later += 1 },
                )
            }
        }
        rule.onNodeWithText("Vida hipotecario · oferta en firme").assertIsDisplayed()
        rule.onNodeWithText("Protección de pagos · prima según tu perfil").assertIsDisplayed()
        rule.onNodeWithText("$89.500 COP / mes").assertIsDisplayed()
        rule.onNodeWithText("Aceptar oferta").assertIsDisplayed()
        rule.onNodeWithText("Revisar despues").assertIsDisplayed()
        rule.onNodeWithTag("mortgage_offer_chevron").assertHasNoClickAction()
        rule.onNodeWithTag("action_accept_mortgage").performClick()
        rule.onNodeWithTag("action_review_later").performClick()
        assertEquals(1, accepted)
        assertEquals(1, later)
    }

    @Test
    fun givenAnotherCoverage_whenShown_thenThatLineReplacesTheSample() {
        val offer = ShowMortgageOffer().show(coverage = "Amparo de saldo", prima = 12_000L)
        rule.setContent {
            SolventaTheme {
                OfertaHipotecarioScreen(
                    offer = offer,
                    onAccept = {},
                    onReviewLater = {},
                    modifier = Modifier,
                )
            }
        }
        rule.onNodeWithText("Vida hipotecario · oferta en firme").assertIsDisplayed()
        rule.onNodeWithText("Amparo de saldo").assertIsDisplayed()
        rule.onNodeWithText("$12.000 COP / mes").assertIsDisplayed()
    }
}
