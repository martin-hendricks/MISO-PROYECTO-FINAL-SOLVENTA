package com.grupo8_uniandes.solventa.shell

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import com.grupo8_uniandes.solventa.ui.shell.ConsentimientoRevocadoScreen
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class ConsentimientoRevocadoScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenTheScreen_whenShown_thenItExplainsTheRevocationAndOffersANewQuote() {
        var newQuote = 0
        var home = 0
        rule.setContent {
            SolventaTheme {
                ConsentimientoRevocadoScreen(
                    onNewQuote = { newQuote += 1 },
                    onHome = { home += 1 },
                )
            }
        }

        rule.onNodeWithTag("screen_consent_revoked").assertIsDisplayed()
        rule.onNodeWithTag("solventa_status_mark_error").assertIsDisplayed()
        rule.onNodeWithText("No pudimos emitir la póliza").assertIsDisplayed()
        rule.onNodeWithText(
            "Revocaste la autorización para usar tus datos en el perfilamiento. Vuelve a cotizar para continuar.",
        ).assertIsDisplayed()
        rule.onNodeWithTag("action_consent_revoked_new_quote").performClick()
        rule.onNodeWithTag("action_consent_revoked_home").performClick()
        assertEquals(1, newQuote)
        assertEquals(1, home)
    }
}
