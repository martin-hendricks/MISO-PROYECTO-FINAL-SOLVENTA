package com.grupo8_uniandes.solventa.policy

import android.content.Intent
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.test.core.app.ActivityScenario
import androidx.test.core.app.ApplicationProvider
import com.grupo8_uniandes.solventa.MainActivity
import com.grupo8_uniandes.solventa.domain.bff.issuance.WalletEntry
import com.grupo8_uniandes.solventa.policy.PolicyDetailUiState
import com.grupo8_uniandes.solventa.policy.PolicyPhase
import com.grupo8_uniandes.solventa.policy.WalletPhase
import com.grupo8_uniandes.solventa.ui.shell.PolizaDetalleScreen
import com.grupo8_uniandes.solventa.ui.shell.PolizasScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.After
import org.junit.Rule
import org.junit.Test

class PolizasConsultaTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    private var scenario: ActivityScenario<MainActivity>? = null

    @After
    fun close() {
        scenario?.close()
    }

    @Test
    fun givenTheReviewSet_whenPolizasOpens_thenBothCardsAreShownAndTheEmptyPromptIsAbsent() {
        openShell()
        rule.onNodeWithText("Polizas").performClick()
        rule.onNodeWithTag("tab_Polizas").assertIsSelected()
        rule.onNodeWithText("POL-88219-CO").assertIsDisplayed()
        rule.onNodeWithText("POL-11002-CO").assertIsDisplayed()
        rule.onNodeWithText("Por vencer · en 7 días").assertIsDisplayed()
        rule.onNodeWithText("Cada póliza indica qué hacer en un siniestro según su ramo. La renovación la confirma un operador.").assertIsDisplayed()
        rule.onAllNodesWithText("¿Aún no tienes pólizas? Puedes pedir tu primera cotización aquí mismo.").assertCountEquals(0)
        rule.onAllNodesWithText("Renovar").assertCountEquals(0)
        rule.onAllNodesWithText("Modificar").assertCountEquals(0)
        rule.onAllNodesWithText("Cancelar").assertCountEquals(0)
        rule.onAllNodesWithTag("tab_Avisos").assertCountEquals(0)
        rule.onNodeWithTag("action_open_policy_POL-88219-CO").performClick()
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithText("Robo y Pantalla").assertIsDisplayed()
        rule.onNodeWithTag("action_expiry_notices").assertIsDisplayed()
    }

    @Test
    fun givenNoPolicies_whenTheListIsShown_thenTheEmptyPromptReplacesTheCards() {
        rule.setContent {
            SolventaTheme {
                PolizasScreen(
                    policies = emptyList(),
                    phase = WalletPhase.Failed,
                    onOpenPolicy = {},
                    onNewQuote = {},
                )
            }
        }
        rule.onNodeWithText("¿Aún no tienes pólizas? Puedes pedir tu primera cotización aquí mismo.").assertIsDisplayed()
        rule.onNodeWithText("Solicitar cotización").assertIsDisplayed()
        rule.onAllNodesWithText("POL-88219-CO").assertCountEquals(0)
        rule.onAllNodesWithTag("action_request_quote").assertCountEquals(1)
    }

    @Test
    fun givenASavedConsultation_whenItRecovers_thenTheNoticeStaysOnTheSameScreens() {
        val card = WalletEntry(
            "POL-88219-CO",
            "Protección de dispositivo",
            "Robo, Pantalla, Hurto",
            "vigente",
            "2027-03-12",
        )
        rule.setContent {
            SolventaTheme {
                PolizasScreen(
                    policies = listOf(card),
                    phase = WalletPhase.Ready,
                    notice = true,
                    onOpenPolicy = {},
                    onNewQuote = {},
                )
            }
        }
        rule.onNodeWithTag("screen_polizas").assertIsDisplayed()
        rule.onNodeWithText("POL-88219-CO").assertIsDisplayed()
        rule.onNodeWithTag("policy_sync_notice").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_sync").assertCountEquals(0)

        rule.setContent {
            SolventaTheme {
                PolizaDetalleScreen(
                    state = PolicyDetailUiState(
                        phase = PolicyPhase.Ready,
                        numero = "POL-88219-CO",
                        ramo = "Protección de dispositivo",
                        resumen = "Robo y Pantalla",
                        estado = "vigente",
                        venceEn = "2027-03-12",
                        queHacer = "guia",
                        notice = true,
                    ),
                )
            }
        }
        rule.onNodeWithTag("screen_poliza_detalle").assertIsDisplayed()
        rule.onNodeWithTag("policy_numero").assertIsDisplayed()
        rule.onNodeWithTag("policy_sync_notice").assertIsDisplayed()
        rule.onAllNodesWithTag("screen_sync").assertCountEquals(0)
    }

    private fun openShell() {
        val intent = Intent(ApplicationProvider.getApplicationContext(), MainActivity::class.java)
            .putExtra(MainActivity.EXTRA_ENTER_SIGNED_IN_SHELL, true)
        scenario = ActivityScenario.launch(intent)
        rule.waitUntil(timeoutMillis = 30_000) {
            rule.onAllNodesWithTag("bottom_bar").fetchSemanticsNodes().isNotEmpty()
        }
    }
}
