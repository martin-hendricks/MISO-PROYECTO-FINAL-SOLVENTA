package com.grupo8_uniandes.solventa.policy

import android.content.Intent
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertTextEquals
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.MainActivity
import org.junit.After
import org.junit.Before
import org.junit.Rule
import org.junit.Test

class PolizaEmitidaTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    private lateinit var scenario: ActivityScenario<MainActivity>

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
        rule.onNodeWithText("Póliza emitida · Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithTag("issued_policy_id").assertTextEquals("POL-88219-CO")
        rule.onNodeWithText("Paso 4 de 4: aceptaste la oferta y la prima quedó pagada. Consulta coberturas en Pólizas.").assertIsDisplayed()
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
        rule.onNodeWithTag("action_issued_policy").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithTag("policy_numero").assertTextEquals("POL-88219-CO")
    }

    @Test
    fun givenTheIssuedPolicy_whenIrAlInicio_thenInicioOpens() {
        rule.onNodeWithText("Aceptar oferta").performClick()
        rule.onNodeWithTag("action_issued_home").performClick()
        rule.onNodeWithTag("screen_inicio").assertIsDisplayed()
    }
}
