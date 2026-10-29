package com.grupo8_uniandes.solventa.registration

import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.junit4.createComposeRule
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import androidx.compose.ui.test.performClick
import androidx.compose.ui.test.performScrollTo
import com.grupo8_uniandes.solventa.ui.registration.LivenessScreen
import com.grupo8_uniandes.solventa.ui.registration.LivenessUiState
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Assert.assertEquals
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.RobolectricTestRunner
import org.robolectric.annotation.Config

@RunWith(RobolectricTestRunner::class)
@Config(qualifiers = "w480dp-h2000dp")
class LivenessScreenTest {
    @get:Rule
    val rule = createComposeRule()

    @Test
    fun givenSavedFields_whenContinuar_thenCopyMatchesAndTheStepAdvances() {
        var continued = 0
        rule.setContent {
            SolventaTheme {
                LivenessScreen(
                    state = LivenessUiState(
                        givenName = "Camila",
                        surnames = "Restrepo",
                        email = "camila@correo.com",
                        documentType = "CC",
                        documentTypeOptions = listOf("CC", "CE", "PA"),
                        documentNumber = "1023456789",
                        password = "secret",
                    ),
                    onGivenName = {},
                    onSurnames = {},
                    onEmail = {},
                    onDocumentType = {},
                    onDocumentNumber = {},
                    onPassword = {},
                    onContinue = { continued += 1 },
                    onExistingAccount = {},
                )
            }
        }

        rule.onNodeWithTag("screen_prueba_de_vida").assertIsDisplayed()
        rule.onNodeWithText("Paso 3 de 4 · Prueba de vida").assertIsDisplayed()
        rule.onNodeWithText("Prueba de vida").assertIsDisplayed()
        rule.onNodeWithText(
            "Una selfie confirma que eres tú. Si la verificación simulada no pasa, sigues con tu documento.",
        ).assertIsDisplayed()
        rule.onNodeWithText("Camila").assertIsDisplayed()
        rule.onNodeWithTag("action_liveness_continuar").performScrollTo().performClick()
        assertEquals(1, continued)
    }
}
