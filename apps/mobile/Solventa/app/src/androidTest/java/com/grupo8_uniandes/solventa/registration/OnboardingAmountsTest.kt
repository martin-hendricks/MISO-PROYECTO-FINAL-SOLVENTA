package com.grupo8_uniandes.solventa.registration

import androidx.activity.ComponentActivity
import androidx.compose.ui.test.assertCountEquals
import androidx.compose.ui.test.assertIsDisplayed
import androidx.compose.ui.test.assertIsNotEnabled
import androidx.compose.ui.test.junit4.createAndroidComposeRule
import androidx.compose.ui.test.onAllNodesWithText
import androidx.compose.ui.test.onNodeWithTag
import androidx.compose.ui.test.onNodeWithText
import com.grupo8_uniandes.solventa.ui.registration.OnboardingScreen
import com.grupo8_uniandes.solventa.ui.registration.OnboardingUiState
import com.grupo8_uniandes.solventa.ui.theme.SolventaTheme
import org.junit.Rule
import org.junit.Test

class OnboardingAmountsTest {
    @get:Rule
    val rule = createAndroidComposeRule<ComponentActivity>()

    @Test
    fun givenANewAccount_whenTheScreenIsShown_thenIncomeAndSpendingAreEmpty() {
        rule.setContent {
            SolventaTheme {
                OnboardingScreen(
                    state = OnboardingUiState(),
                    onGivenName = {},
                    onSurnames = {},
                    onEmail = {},
                    onDocumentType = {},
                    onDocumentNumber = {},
                    onPassword = {},
                    onPasswordConfirm = {},
                    onPhotoAttached = {},
                    onPhotoDeclined = {},
                    onHabeasData = {},
                    onContinue = {},
                    onExistingAccount = {},
                )
            }
        }
        rule.onNodeWithText("Paso 3 de 4 · Crea tu cuenta").assertIsDisplayed()
        rule.onNodeWithText("Ingresos y gastos mensuales en COP. El ingreso debe ser mayor que cero.").assertIsDisplayed()
        rule.onNodeWithText("Ingresos mensuales").assertIsDisplayed()
        rule.onNodeWithText("Mayor que cero · COP").assertIsDisplayed()
        rule.onNodeWithText("Gastos mensuales").assertIsDisplayed()
        rule.onNodeWithText("Monto mensual en COP").assertIsDisplayed()
        rule.onNodeWithTag("field_ingresos").assertIsDisplayed()
        rule.onNodeWithTag("field_gastos").assertIsDisplayed()
        rule.onAllNodesWithText("$4.500.000").assertCountEquals(0)
        rule.onAllNodesWithText("$1.200.000").assertCountEquals(0)
        rule.onNodeWithText("Continuar").assertIsNotEnabled()
    }
}
