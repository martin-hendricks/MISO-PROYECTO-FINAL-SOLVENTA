package com.grupo8_uniandes.solventa.shell

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.ui.shell.SuscripcionRechazadaScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class SuscripcionRechazadaScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenTheScreen_whenShown_thenTheRejectionCopyAndActionsAreVisible() {
        var home = 0
        var understood = 0
        rule.setContent {
            SolventaTheme {
                SuscripcionRechazadaScreen(
                    onHome = { home += 1 },
                    onUnderstood = { understood += 1 },
                )
            }
        }

        rule.onNodeWithTag("screen_rejection").assertIsDisplayed()
        rule.onNodeWithTag("solventa_status_mark_error").assertIsDisplayed()
        rule.onNodeWithText("No pudimos emitir Protección de dispositivo").assertIsDisplayed()
        rule.onNodeWithText("La suscripción automática rechazó el riesgo del dispositivo cotizado.").assertIsDisplayed()
        rule.onNodeWithTag("action_rejection_home").performClick()
        rule.onNodeWithTag("action_rejection_understood").performClick()
        assertEquals(1, home)
        assertEquals(1, understood)
    }
}
