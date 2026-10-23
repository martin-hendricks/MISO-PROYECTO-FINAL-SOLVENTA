package com.grupo8_uniandes.solventa.quote

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteField
import com.grupo8_uniandes.solventa.ui.shell.CotizacionScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class CotizacionScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenTheForm_whenShown_thenTheLineIsLockedAndAgeIsUnanswered() {
        rule.setContent {
            SolventaTheme {
                CotizacionScreen(
                    state = QuoteUiState(),
                    onValueChange = {},
                    onBrandChange = {},
                    onAge = {},
                    onCotizar = {},
                    onCancel = {},
                )
            }
        }

        rule.onNodeWithTag("screen_cotizacion").assertIsDisplayed()
        rule.onNodeWithText("Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("Robo, Pantalla, Hurto calificado").assertIsDisplayed()
        rule.onNodeWithText("Valor del dispositivo").assertIsDisplayed()
        rule.onNodeWithText("Marca y modelo").assertIsDisplayed()
        rule.onNodeWithText("¿Equipo con más de 12 meses?").assertIsDisplayed()
        rule.onNodeWithTag("answer_yes").assertIsDisplayed()
        rule.onNodeWithTag("answer_no").assertIsDisplayed()
        rule.onNodeWithTag("action_quote").assertIsDisplayed()
        rule.onNodeWithText("Cancelar").assertIsDisplayed()
        rule.onAllNodesWithText("Placa").assertCountEquals(0)
        rule.onAllNodesWithText("IMEI").assertCountEquals(0)
        rule.onAllNodesWithText("Hogar").assertCountEquals(0)
    }

    @Test
    fun givenValueGapAndYes_whenShown_thenTheGapAndFilledYesAreVisible() {
        show(
            QuoteUiState(gap = QuoteField.Value, olderThan12Months = true),
        )
        rule.onNodeWithText("Completa este dato").assertIsDisplayed()
    }

    @Test
    fun givenBrandGapPendingAndFailure_whenShown_thenThoseMessagesAreVisible() {
        show(
            QuoteUiState(
                gap = QuoteField.Brand,
                olderThan12Months = false,
                pending = true,
                failed = true,
            ),
        )
        rule.onAllNodesWithText("Completa este dato").assertCountEquals(1)
        rule.onNodeWithTag("quote_progress").assertIsDisplayed()
        rule.onNodeWithTag("quote_failed").assertIsDisplayed()
    }

    @Test
    fun givenAgeGap_whenShown_thenTheAgeMessageIsVisible() {
        show(QuoteUiState(gap = QuoteField.Age))
        rule.onNodeWithTag("age_required").assertIsDisplayed()
    }

    private fun show(state: QuoteUiState) {
        rule.setContent {
            SolventaTheme {
                CotizacionScreen(
                    state = state,
                    onValueChange = {},
                    onBrandChange = {},
                    onAge = {},
                    onCotizar = {},
                    onCancel = {},
                    modifier = androidx.compose.ui.Modifier,
                )
            }
        }
    }
}
