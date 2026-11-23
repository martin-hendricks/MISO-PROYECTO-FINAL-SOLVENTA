package com.grupo8_uniandes.solventa.claim

import androidx.activity.ComponentActivity
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Text
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.R
import com.grupo8_uniandes.solventa.domain.bff.claim.OpenParametricPayment
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.shell.ParametricoScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class ParametricoTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Before
    fun accessibilityChecks() {
        rule.enableAccessibilityChecks()
    }

    @Test
    fun givenTheStoredPayment_whenTheSummaryIsShown_thenTheNoticeHasNoThirdPartyMessage() {
        show()
        rule.onNodeWithText("Pago automatico").assertIsDisplayed()
        rule.onNodeWithText("Pago automático realizado").assertIsDisplayed()
        rule.onNodeWithText("Clima y vuelos · vuelo AV-234").assertIsDisplayed()
        rule.onNodeWithText("Póliza POL-77310 · no es el cobro de la prima").assertIsDisplayed()
        rule.onNodeWithText("$180.000 COP depositados").assertIsDisplayed()
        rule.onNodeWithText("Depósito automático sobre la póliza relacionada. No repite el cobro de la prima.").assertIsDisplayed()
        rule.onNodeWithText("Pago de renovación automática").assertIsDisplayed()
        rule.onNodeWithText("Apagado. Opta esa póliza a renovar su prima.").assertIsDisplayed()
        rule.onAllNodesWithText("No tienes que reportar nada", substring = true).assertCountEquals(0)
        rule.onNodeWithTag("tab_Siniestros").assertIsSelected()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)
        rule.onAllNodesWithText("tercero", substring = true).assertCountEquals(0)
    }

    @Test
    fun givenThePushOpensTheSummary_whenItIsShown_thenItIsTheSameNotice() {
        show()
        rule.onNodeWithTag("screen_parametrico").assertIsDisplayed()
        rule.onNodeWithText("Pago automático realizado").assertIsDisplayed()
        rule.onAllNodesWithTag("notification_bell").assertCountEquals(0)
        rule.onAllNodesWithText("tercero", substring = true).assertCountEquals(0)
    }

    @Test
    fun givenTheReceipt_whenItIsChosen_thenTheSummaryStays() {
        show()
        rule.onNodeWithText("Volver a siniestros").assertIsDisplayed()
        rule.onNodeWithText("Descargar comprobante").performClick()
        rule.onNodeWithTag("screen_parametrico").assertIsDisplayed()
        rule.onNodeWithText("$180.000 COP depositados").assertIsDisplayed()
    }

    private fun show() {
        rule.setContent {
            SolventaTheme {
                Box(Modifier.fillMaxSize()) {
                    Text(stringResource(R.string.parametric_title))
                    ParametricoScreen(
                        notice = OpenParametricPayment.review,
                        onBack = {},
                        onDownload = {},
                    )
                    SolventaBottomBar(
                        selected = Destination.Siniestros,
                        onSelect = {},
                        modifier = Modifier.align(Alignment.BottomCenter),
                    )
                }
            }
        }
    }
}
