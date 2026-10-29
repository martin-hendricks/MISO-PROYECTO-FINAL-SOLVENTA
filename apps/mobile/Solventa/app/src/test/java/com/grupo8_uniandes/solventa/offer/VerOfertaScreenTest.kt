package com.grupo8_uniandes.solventa.offer

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.domain.bff.offer.formatOfferDate
import com.grupo8_uniandes.solventa.domain.region.Region
import com.grupo8_uniandes.solventa.domain.region.formatPremium
import com.grupo8_uniandes.solventa.ui.shell.VerOfertaScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config
import java.math.BigDecimal

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class VerOfertaScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenInForce_whenShown_thenPremiumAndAcceptAndNoFallback() {
        val premium = formatPremium(BigDecimal("89000"), "COP", Region.Colombia)
        val date = formatOfferDate("2026-10-01", Region.Colombia)
        show(
            OfferUiState(
                phase = OfferPhase.Ready,
                premiumText = premium,
                endDateText = date,
                acceptEnabled = true,
                expired = false,
                cotizacionId = "COT-1042",
                ramo = "Protección de dispositivo",
            ),
        )

        rule.onNodeWithTag("screen_ver_oferta").assertIsDisplayed()
        rule.onNodeWithText("Prima $premium").assertIsDisplayed()
        rule.onNodeWithText("Vence $date · sigue: emitir y pagar").assertIsDisplayed()
        rule.onNodeWithText("Protección de dispositivo · cotización lista. Si aceptas, se emite la póliza y se cobra la prima.").assertIsDisplayed()
        rule.onNodeWithTag("action_accept_offer").assertIsEnabled()
        rule.onNodeWithTag("action_not_now").assertIsDisplayed()
        rule.onAllNodesWithTag("offer_expired").assertCountEquals(0)
        rule.onAllNodesWithText("Usamos un valor de respaldo").assertCountEquals(0)
    }

    @Test
    fun givenExpired_whenShown_thenAcceptIsDisabledAndQuoteAgainIsOffered() {
        show(
            OfferUiState(
                phase = OfferPhase.Ready,
                premiumText = "$89.000 COP",
                endDateText = formatOfferDate("2026-10-01", Region.Colombia),
                acceptEnabled = false,
                expired = true,
                cotizacionId = "COT-1042",
            ),
        )

        rule.onNodeWithTag("offer_expired").assertIsDisplayed()
        rule.onNodeWithText("La oferta está vencida").assertIsDisplayed()
        rule.onNodeWithTag("action_accept_offer").assertIsNotEnabled()
        rule.onNodeWithTag("action_quote_again").assertIsDisplayed()
        rule.onAllNodesWithTag("action_not_now").assertCountEquals(0)
        rule.onNodeWithText("Prima $89.000 COP").assertIsDisplayed()
    }

    @Test
    fun givenPending_whenShown_thenThePriceIsAbsent() {
        show(OfferUiState(phase = OfferPhase.Pending))
        rule.onNodeWithTag("offer_pending").assertIsDisplayed()
        rule.onAllNodesWithTag("offer_premium").assertCountEquals(0)
    }

    @Test
    fun givenADisabledAccept_whenShown_thenTheButtonStays() {
        show(
            OfferUiState(
                phase = OfferPhase.Ready,
                premiumText = "COP 1",
                endDateText = "1 ene 2027",
                acceptEnabled = false,
                expired = false,
            ),
        )
        rule.onNodeWithTag("action_accept_offer").assertIsNotEnabled()
    }

    @Test
    fun givenFailed_whenShown_thenAcceptIsAbsent() {
        show(OfferUiState(phase = OfferPhase.Failed))
        rule.onNodeWithTag("offer_failed").assertIsDisplayed()
        rule.onAllNodesWithTag("action_accept_offer").assertCountEquals(0)
    }

    private fun show(state: OfferUiState) {
        rule.setContent {
            SolventaTheme {
                VerOfertaScreen(
                    state = state,
                    onAccept = {},
                    onQuoteAgain = {},
                    onDecline = {},
                    modifier = androidx.compose.ui.Modifier,
                )
            }
        }
    }
}
