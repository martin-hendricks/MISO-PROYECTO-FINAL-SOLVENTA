package com.grupo8_uniandes.solventa.policy

import android.content.Intent
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.accessibility.enableAccessibilityChecks
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.issuance.confirmReviewCard
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class PolizaEmitidaTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    private lateinit var scenario: ActivityScenario<MainActivity>

    @Before
    fun accessibilityChecks() {
        rule.enableAccessibilityChecks()
    }

    @Before
    fun leaveSplash() {
        val intent = Intent(ApplicationProvider.getApplicationContext(), MainActivity::class.java)
            .putExtra(MainActivity.EXTRA_ENTER_SIGNED_IN_SHELL, true)
        scenario = ActivityScenario.launch(intent)
        rule.waitUntil(timeoutMillis = 30_000) {
            rule.onAllNodesWithTag("bottom_bar").fetchSemanticsNodes().isNotEmpty()
        }
    }

    @After
    fun close() {
        scenario.close()
    }

    @Test
    fun givenASuccessfulAccept_whenIssued_thenTheNumberAndTheTwoActionsAreShown() {
        rule.onNodeWithText("Aceptar oferta").performClick()
        rule.confirmReviewCard()
        rule.onNodeWithText("Póliza emitida · Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithTag("issued_policy_id").assertTextEquals("POL-88219-CO")
        rule.onNodeWithText("Resumen de la prima aprobada. La póliza ya está emitida.").assertIsDisplayed()
        rule.onNodeWithText("Prima").assertIsDisplayed()
        rule.onNodeWithText("$42.000").assertIsDisplayed()
        rule.onNodeWithText("Moneda").assertIsDisplayed()
        rule.onNodeWithText("COP").assertIsDisplayed()
        rule.onNodeWithText("Referencia de pago").assertIsDisplayed()
        rule.onNodeWithText("PAY-44218").assertIsDisplayed()
        rule.onNodeWithText("Pago de renovación automática").assertIsDisplayed()
        rule.onNodeWithText("Apagado. Renueva la prima de esta póliza. No cobra ahora.").assertIsDisplayed()
        rule.onAllNodesWithText("Paso 4 de 4: aceptaste la oferta y la prima quedó pagada. Consulta coberturas en Pólizas.").assertCountEquals(0)
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onNodeWithTag("action_issued_policy").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithTag("policy_numero", useUnmergedTree = true).assertTextEquals("POL-88219-CO")
    }

    @Test
    fun givenTheIssuedPolicy_whenIrAlInicio_thenInicioOpens() {
        rule.onNodeWithText("Aceptar oferta").performClick()
        rule.confirmReviewCard()
        rule.onNodeWithTag("action_issued_home").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
    }
}
