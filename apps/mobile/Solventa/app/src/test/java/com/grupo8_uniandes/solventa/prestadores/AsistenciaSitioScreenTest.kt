package com.grupo8_uniandes.solventa.prestadores

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsEnabled
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.domain.bff.claim.AssistanceForm
import com.grupo8_uniandes.solventa.domain.bff.issuance.PolicyEntry
import com.grupo8_uniandes.solventa.ui.shell.AsistenciaSitioScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner

@RunWith(RobolectricTestRunner::class)
class AsistenciaSitioScreenTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenNoPolicyInForce_whenAssistanceOpens_thenContinueStaysDisabled() {
        rule.setContent {
            SolventaTheme {
                AsistenciaSitioScreen(
                    form = FORM,
                    policies = emptyList(),
                    policiesLoaded = true,
                    onContinue = {},
                    onCancel = {},
                )
            }
        }

        rule.onNodeWithText("No tienes una póliza vigente para reportar un siniestro.").assertIsDisplayed()
        rule.onNodeWithTag("action_continuar_evidencia").assertIsNotEnabled()
    }

    @Test
    fun givenAPolicyInForce_whenAssistanceOpens_thenContinueIsEnabled() {
        rule.setContent {
            SolventaTheme {
                AsistenciaSitioScreen(
                    form = FORM,
                    policies = listOf(PolicyEntry("POL-1", "SOAT", "moto", "vigente", "2027-01-01")),
                    policiesLoaded = true,
                    onContinue = {},
                    onCancel = {},
                )
            }
        }

        rule.onAllNodesWithTag("assistance_no_policy").assertCountEquals(0)
        rule.onNodeWithTag("action_continuar_evidencia").assertIsEnabled()
    }

    private companion object {
        val FORM = AssistanceForm(
            registration = "Registramos el pedido.",
            policyValue = "",
            dateValue = "2026-03-12",
            descriptionValue = "Choque",
            placeValue = "Calle 72",
        )
    }
}
