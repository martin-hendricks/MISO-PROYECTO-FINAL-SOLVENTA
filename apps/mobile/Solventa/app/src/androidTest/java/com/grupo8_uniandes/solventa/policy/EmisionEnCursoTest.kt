package com.grupo8_uniandes.solventa.policy

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithTag
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.ui.shell.EmisionEnCursoScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test

class EmisionEnCursoTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenIssuanceInProgress_whenShown_thenStepThreeHasNoWayOut() {
        rule.setContent {
            SolventaTheme {
                EmisionEnCursoScreen()
            }
        }
        rule.onNodeWithText("Emitiendo tu póliza · paso 3 de 4").assertIsDisplayed()
        rule.onNodeWithTag("emision_body").assertIsDisplayed()
        rule.onNodeWithText("Paso 3 de 4: cobramos la prima y firmamos. Al terminar, tu póliza vive en Pólizas.").assertIsDisplayed()
        rule.onAllNodesWithTag("action_finish_issuing").assertCountEquals(0)
        rule.onAllNodesWithTag("bottom_bar").assertCountEquals(0)
    }
}
