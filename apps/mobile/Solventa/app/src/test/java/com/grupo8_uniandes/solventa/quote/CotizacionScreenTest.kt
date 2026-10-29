package com.grupo8_uniandes.solventa.quote

import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.ui.Modifier
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.assertTextContains
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteInput
import com.grupo8_uniandes.solventa.domain.bff.offer.QuoteLine
import com.grupo8_uniandes.solventa.ui.shell.CotizacionScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
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
        show(QuoteUiState(value = "48900"))

        rule.onNodeWithTag("screen_cotizacion").assertIsDisplayed()
        rule.onNodeWithText("Tipo de seguro").assertIsDisplayed()
        rule.onNodeWithText("Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithTag("quote_line_hint").assertIsDisplayed()
            .assertTextContains("no es el valor del dispositivo", substring = true)
        rule.onNodeWithTag("quote_ramo_note").assertIsDisplayed()
        rule.onNodeWithText("Valor del dispositivo (COP)").assertIsDisplayed()
        rule.onNodeWithText("$48.900").assertIsDisplayed()
        rule.onNodeWithText("Marca / modelo").assertIsDisplayed()
        rule.onNodeWithText("¿El equipo tiene más de 12 meses?").assertIsDisplayed()
        rule.onNodeWithTag("answer_yes").assertIsDisplayed()
        rule.onNodeWithTag("answer_no").assertIsDisplayed()
        rule.onNodeWithTag("action_quote").assertIsDisplayed()
        rule.onNodeWithText("Cancelar").assertIsDisplayed()
        rule.onAllNodesWithText("Placa").assertCountEquals(0)
        rule.onAllNodesWithText("IMEI").assertCountEquals(0)
        rule.onAllNodesWithText("Hogar").assertCountEquals(0)
        rule.onAllNodesWithText("SOAT").assertCountEquals(0)
    }

    @Test
    fun givenTheClosedLine_whenTapped_thenTheMenuOpens() {
        var opened = false
        show(QuoteUiState(), onMenu = { opened = it })

        rule.onNodeWithTag("quote_line").performClick()

        assertTrue(opened)
    }

    @Test
    fun givenTheMenu_whenOpened_thenTheSixLinesAreListed() {
        var chosen = QuoteLine.Device
        show(QuoteUiState(menuOpen = true), onLine = { chosen = it })

        rule.onNodeWithTag("quote_option_device").assertIsDisplayed()
        rule.onNodeWithTag("quote_option_life").assertIsDisplayed()
        rule.onNodeWithTag("quote_option_climate").assertIsDisplayed()
        rule.onNodeWithTag("quote_option_mortgage").assertIsDisplayed()
        rule.onNodeWithTag("quote_option_payments").assertIsDisplayed()
        rule.onNodeWithText("Microseguro de vida").assertIsDisplayed()
        rule.onNodeWithText("Clima y vuelos").assertIsDisplayed()
        rule.onNodeWithText("Vida hipotecario").assertIsDisplayed()
        rule.onNodeWithText("Protección de pagos").assertIsDisplayed()
        rule.onNodeWithText("Seguros de viaje").assertIsDisplayed()
        rule.onNodeWithTag("quote_option_travel").performClick()

        assertEquals(QuoteLine.Travel, chosen)
    }

    @Test
    fun givenTravel_whenShown_thenDeviceFieldsAreGone() {
        show(QuoteUiState(line = QuoteLine.Travel))

        rule.onNodeWithTag("field_destination").assertIsDisplayed()
        rule.onNodeWithTag("field_duration").assertIsDisplayed()
        rule.onNodeWithText("Destino").assertIsDisplayed()
        rule.onNodeWithText("Duración (días)").assertIsDisplayed()
        rule.onNodeWithTag("quote_line_hint")
            .assertTextContains("No pidas valor ni marca de un dispositivo.", substring = true)
        rule.onAllNodesWithText("Valor del dispositivo (COP)").assertCountEquals(0)
        rule.onAllNodesWithText("Marca / modelo").assertCountEquals(0)
        rule.onAllNodesWithText("¿El equipo tiene más de 12 meses?").assertCountEquals(0)
        rule.onAllNodesWithTag("answer_yes").assertCountEquals(0)
    }

    @Test
    fun givenValueGapAndYes_whenShown_thenTheGapAndFilledYesAreVisible() {
        show(QuoteUiState(gap = QuoteInput.Value, olderThan12Months = true))
        rule.onNodeWithText("Completa este dato").assertIsDisplayed()
    }

    @Test
    fun givenBrandGapPendingAndFailure_whenShown_thenThoseMessagesAreVisible() {
        show(
            QuoteUiState(
                gap = QuoteInput.Brand,
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
        show(QuoteUiState(gap = QuoteInput.Age))
        rule.onNodeWithTag("age_required").assertIsDisplayed()
    }

    @Test
    fun givenLife_whenShown_thenItsFieldsAndAGapAreVisible() {
        show(QuoteUiState(line = QuoteLine.Life, gap = QuoteInput.SumInsured), modifier = Modifier.fillMaxSize())
        rule.onNodeWithTag("field_sum_insured").assertIsDisplayed()
        rule.onNodeWithTag("field_age_years").assertIsDisplayed()
        rule.onNodeWithText("Suma asegurada (COP)").assertIsDisplayed()
    }

    @Test
    fun givenClimate_whenShown_thenTextAndNumberFieldsAreVisible() {
        show(QuoteUiState(line = QuoteLine.Climate, gap = QuoteInput.Event))
        rule.onNodeWithTag("field_event").assertIsDisplayed()
        rule.onNodeWithTag("field_threshold").assertIsDisplayed()
        rule.onNodeWithText("Tipo de evento").assertIsDisplayed()
        rule.onNodeWithText("Umbral (horas)").assertIsDisplayed()
        rule.onAllNodesWithTag("field_reference").assertCountEquals(0)
    }

    @Test
    fun givenMortgage_whenShown_thenCreditFieldsAreVisible() {
        show(QuoteUiState(line = QuoteLine.Mortgage, gap = QuoteInput.CreditTerm))
        rule.onNodeWithTag("field_credit_value").assertIsDisplayed()
        rule.onNodeWithTag("field_credit_term").assertIsDisplayed()
        rule.onNodeWithText("Valor del crédito (COP)").assertIsDisplayed()
        rule.onNodeWithText("Plazo (años)").assertIsDisplayed()
    }

    @Test
    fun givenPayments_whenShown_thenInstallmentFieldsAreVisible() {
        show(QuoteUiState(line = QuoteLine.Payments, gap = QuoteInput.Installment))
        rule.onNodeWithTag("field_installment").assertIsDisplayed()
        rule.onNodeWithTag("field_term").assertIsDisplayed()
        rule.onNodeWithText("Cuota mensual (COP)").assertIsDisplayed()
        rule.onNodeWithText("Plazo (meses)").assertIsDisplayed()
    }

    private fun show(
        state: QuoteUiState,
        onMenu: (Boolean) -> Unit = {},
        onLine: (QuoteLine) -> Unit = {},
        modifier: Modifier = Modifier,
    ) {
        rule.setContent {
            SolventaTheme {
                CotizacionScreen(
                    state = state,
                    onMenu = onMenu,
                    onLine = onLine,
                    onValueChange = {},
                    onBrandChange = {},
                    onAge = {},
                    onText = { _, _ -> },
                    onCotizar = {},
                    onCancel = {},
                    modifier = modifier,
                )
            }
        }
    }
}
