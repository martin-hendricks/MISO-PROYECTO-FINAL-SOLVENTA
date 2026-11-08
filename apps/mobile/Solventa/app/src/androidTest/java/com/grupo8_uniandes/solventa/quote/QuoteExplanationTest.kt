package com.grupo8_uniandes.solventa.quote

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteInput
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.quote.QuoteUiState
import com.grupo8_uniandes.solventa.ui.shell.CotizacionScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class QuoteExplanationTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Before
    fun accessibilityChecks() {
        rule.enableAccessibilityChecks()
    }

    @Test
    fun givenARefusedQuote_whenTheScreenIsShown_thenTheServerSentenceStaysAndNoOfferOpens() {
        show("El ratio de gastos supera el porcentaje máximo vigente")
        rule.onNodeWithTag("quote_explanation").assertIsDisplayed()
        rule.onNodeWithText("El ratio de gastos supera el porcentaje máximo vigente").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_oferta").assertCountEquals(0)
    }

    @Test
    fun givenIncomeThatIsNotPositive_whenExplained_thenThatSentenceIsShown() {
        show("El ingreso mensual debe ser mayor que cero")
        rule.onNodeWithText("El ingreso mensual debe ser mayor que cero").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_oferta").assertCountEquals(0)
    }

    private fun show(explanation: String) {
        rule.setContent {
            SolventaTheme {
                CotizacionScreen(
                    state = QuoteUiState(explanation = explanation),
                    onMenu = {},
                    onLine = {},
                    onValueChange = {},
                    onBrandChange = {},
                    onModelChange = {},
                    onAge = {},
                    onText = { _: QuoteInput, _: String -> },
                    onCotizar = {},
                    onCancel = {},
                    region = Region.Colombia,
                )
            }
        }
    }
}
