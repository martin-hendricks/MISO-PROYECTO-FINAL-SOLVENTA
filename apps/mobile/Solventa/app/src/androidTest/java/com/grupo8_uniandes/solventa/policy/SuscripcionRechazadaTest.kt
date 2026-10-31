package com.grupo8_uniandes.solventa.policy

import androidx.compose.foundation.layout.Column
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsSelected
import androidx.compose.ui.test.junit4.createEmptyComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.navigation.Destination
import com.grupo8_uniandes.solventa.ui.components.SolventaBottomBar
import com.grupo8_uniandes.solventa.ui.shell.SuscripcionRechazadaScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test

class SuscripcionRechazadaTest {
    @get:Rule
    val rule = createEmptyComposeRule()

    @Test
    fun givenARefusal_whenShown_thenTheReasonLeavesForInicio() {
        var home = 0
        var understood = 0
        rule.setContent {
            SolventaTheme {
                Column {
                    SuscripcionRechazadaScreen(
                        onHome = { home += 1 },
                        onUnderstood = { understood += 1 },
                    )
                    SolventaBottomBar(selected = Destination.Inicio, onSelect = {})
                }
            }
        }
        rule.onNodeWithText("Resultado de la oferta").assertIsDisplayed()
        rule.onNodeWithText("No pudimos emitir Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("La suscripción automática rechazó el riesgo del dispositivo cotizado.").assertIsDisplayed()
        rule.onAllNodesWithText("POL-88219-CO").assertCountEquals(0)
        rule.onNodeWithTag("tab_Inicio").assertIsSelected()
        rule.onAllNodesWithText("Renovar", substring = true).assertCountEquals(0)
        rule.onNodeWithTag("action_rejection_home").performClick()
        rule.onNodeWithTag("action_rejection_understood").performClick()
        assertEquals(1, home)
        assertEquals(1, understood)
    }
}
