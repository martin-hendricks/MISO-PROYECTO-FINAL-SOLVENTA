package com.grupo8_uniandes.solventa.shell

import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.ui.shell.PolizaEmitidaScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class PolizaEmitidaScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenAnotherRamo_whenIssued_thenTheTitleShowsThatRamo() {
        rule.setContent {
            SolventaTheme {
                PolizaEmitidaScreen(
                    policyId = "POL-SOAT-1",
                    ramo = "SOAT motocicleta",
                    onGoHome = {},
                    onGoPolicy = {},
                )
            }
        }

        rule.onNodeWithTag("screen_issued").assertIsDisplayed()
        rule.onNodeWithText("Póliza emitida · SOAT motocicleta").assertIsDisplayed()
        rule.onAllNodesWithText("Protección de dispositivo", substring = true).assertCountEquals(0)
    }
}
